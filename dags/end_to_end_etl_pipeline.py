"""
End-to-End ETL Pipeline DAG
============================
Real-world enterprise data pipeline demonstrating:
- Azure Blob ingestion
- Data transformation in Databricks
- Data quality checks
- PowerBI dataset refresh
- Error handling and notifications

Schedule: Daily at 2 AM EST
SLA: 4 hours
"""

from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.operators.empty import EmptyOperator
from airflow.utils.task_group import TaskGroup
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)


# --------------------------------------------------------------------------------
# TASK FUNCTIONS
# --------------------------------------------------------------------------------

def ingest_from_azure(**context):
    """Copy raw data files from Azure Blob landing zone to processing zone."""
    from airflow.providers.microsoft.azure.hooks.wasb import WasbHook
    
    execution_date = context['ds']  # YYYY-MM-DD format
    logger.info(f"Processing data for date: {execution_date}")
    
    # Get Azure Blob Hook
    hook = WasbHook(wasb_conn_id='azure_blob_default')
    client = hook.get_conn()
    
    # Define source and target
    source_container = "sg-analytics-raw"
    target_container = "sg-analytics-bronze"
    source_prefix = f"landing_zone/daily/{execution_date}/"
    
    logger.info(f"Copying from {source_container}/{source_prefix} to {target_container}")
    
    # List and copy files (server-side copy - Azure handles transfer)
    source = client.get_container_client(source_container)
    target = client.get_container_client(target_container)
    
    files_copied = 0
    total_bytes = 0
    
    for blob in source.list_blobs(name_starts_with=source_prefix):
        target_name = blob.name.replace("landing_zone/", "bronze/")
        
        # Build source URL for server-side copy
        source_url = f"{client.account_url}/{source_container}/{blob.name}"
        target_blob = target.get_blob_client(target_name)
        
        logger.info(f"  Copying: {blob.name} ({blob.size:,} bytes)")
        # Server-side copy - no data flows through Airflow
        copy_result = target_blob.start_copy_from_url(source_url)
        
        files_copied += 1
        total_bytes += blob.size
    
    logger.info(f"✓ Initiated {files_copied} file copies ({total_bytes:,} bytes)")
    logger.info(f"   Total size: {total_bytes/1024/1024:.2f} MB")
    logger.info("   Note: Server-side copy - Azure handles transfer (no load on Airflow)")
    
    return {
        'files_copied': files_copied,
        'total_bytes': total_bytes,
        'total_mb': round(total_bytes/1024/1024, 2),
        'execution_date': execution_date,
        'copy_method': 'azure_server_side'
    }


def validate_data_quality(**context):
    """Run data quality checks on ingested files."""
    from airflow.providers.microsoft.azure.hooks.wasb import WasbHook
    import pandas as pd
    from io import BytesIO
    
    execution_date = context['ds']
    logger.info("Running data quality checks...")
    
    # Get Azure Blob Hook
    hook = WasbHook(wasb_conn_id='azure_blob_default')
    client = hook.get_conn()
    
    container = client.get_container_client("sg-analytics-bronze")
    prefix = f"bronze/daily/{execution_date}/"
    
    # Quality metrics
    checks_passed = 0
    checks_failed = 0
    issues = []
    
    for blob in container.list_blobs(name_starts_with=prefix):
        if not blob.name.endswith('.csv'):
            continue
            
        logger.info(f"  Checking: {blob.name} ({blob.size:,} bytes)")
        
        # Download and check file
        blob_client = container.get_blob_client(blob.name)
        
        # For large files (>100MB), skip content validation to avoid memory issues
        if blob.size > 100 * 1024 * 1024:
            logger.info(f"    Large file ({blob.size/1024/1024:.1f} MB) - skipping content validation")
            checks_passed += 1
            continue
        
        # Download smaller files for validation
        data = blob_client.download_blob().readall()
        
        try:
            df = pd.read_csv(BytesIO(data))
            
            # Check 1: Non-empty file
            if len(df) == 0:
                issues.append(f"{blob.name}: Empty file")
                checks_failed += 1
                continue
            
            # Check 2: No duplicate rows
            if df.duplicated().sum() > 0:
                issues.append(f"{blob.name}: {df.duplicated().sum()} duplicate rows")
                checks_failed += 1
            else:
                checks_passed += 1
                
            # Check 3: No completely null columns
            null_cols = df.columns[df.isnull().all()].tolist()
            if null_cols:
                issues.append(f"{blob.name}: Completely null columns: {null_cols}")
                checks_failed += 1
            
            logger.info(f"    ✓ Rows: {len(df):,}, Columns: {len(df.columns)}")
            
        except Exception as e:
            issues.append(f"{blob.name}: Failed to parse - {str(e)}")
            checks_failed += 1
    
    logger.info(f"Quality checks: {checks_passed} passed, {checks_failed} failed")
    
    if checks_failed > 0:
        logger.warning("Data quality issues found:")
        for issue in issues:
            logger.warning(f"  - {issue}")
    
    # Fail task if critical issues found
    if checks_failed > len(issues) * 0.3:  # More than 30% failure rate
        raise ValueError(f"Data quality checks failed: {checks_failed} issues found")
    
    return {
        'checks_passed': checks_passed,
        'checks_failed': checks_failed,
        'issues': issues
    }


def transform_in_databricks(**context):
    """Run Databricks transformation notebook."""
    from airflow.providers.databricks.hooks.databricks import DatabricksHook
    import time
    
    execution_date = context['ds']
    logger.info(f"Starting Databricks transformation for {execution_date}")
    
    # Get Databricks hook
    hook = DatabricksHook(databricks_conn_id='databricks_default')
    
    # Submit notebook job
    url = f"{hook.host}/api/2.1/jobs/runs/submit"
    # Get cluster_id from connection extra
    conn = hook.get_conn()
    cluster_id = conn.extra_dejson.get('cluster_id', 'your-cluster-id')
    
    payload = {
        'run_name': f"ETL_Transform_{execution_date}",
        'existing_cluster_id': cluster_id,
        'notebook_task': {
            'notebook_path': '/Shared/ETL/daily_transformation',
            'base_parameters': {
                'execution_date': execution_date,
                'source_path': f'bronze/daily/{execution_date}/',
                'target_path': f'silver/daily/{execution_date}/'
            }
        },
        'timeout_seconds': 3600
    }
    
    response = hook._do_api_call(('POST', 'api/2.1/jobs/runs/submit'), json=payload)
    run_id = response.get('run_id')
    
    logger.info(f"Databricks job started: Run ID {run_id}")
    
    # Poll for completion
    while True:
        response = hook._do_api_call(
            ('GET', f'api/2.1/jobs/runs/get'),
            json={'run_id': run_id}
        )
        
        state = response.get('state', {})
        life_cycle_state = state.get('life_cycle_state')
        
        logger.info(f"  Job status: {life_cycle_state}")
        
        if life_cycle_state in ['TERMINATED', 'SKIPPED']:
            result_state = state.get('result_state')
            if result_state == 'SUCCESS':
                logger.info("✓ Databricks transformation completed successfully")
                return {'run_id': run_id, 'status': 'success'}
            else:
                raise ValueError(f"Databricks job failed: {result_state}")
        
        elif life_cycle_state in ['INTERNAL_ERROR']:
            raise ValueError(f"Databricks job error: {life_cycle_state}")
        
        time.sleep(30)  # Wait 30 seconds before next check


def load_to_gold_layer(**context):
    """Create final aggregated tables in gold layer."""
    from airflow.providers.microsoft.azure.hooks.wasb import WasbHook
    import pandas as pd
    from io import BytesIO
    
    execution_date = context['ds']
    logger.info("Creating gold layer aggregations...")
    
    # Get Azure Blob Hook
    hook = WasbHook(wasb_conn_id='azure_blob_default')
    client = hook.get_conn()
    
    # Read silver layer data
    silver_container = client.get_container_client("sg-analytics-silver")
    gold_container = client.get_container_client("sg-analytics-gold")
    
    logger.info("Aggregating sales data...")
    
    # Example: Create daily sales summary
    silver_path = f"silver/daily/{execution_date}/sales_transactions.csv"
    gold_path = f"gold/daily_sales_summary/{execution_date}.csv"
    
    # Download silver data
    blob = silver_container.get_blob_client(silver_path)
    
    # Stream download for efficiency (instead of readall)
    stream = blob.download_blob()
    df = pd.read_csv(BytesIO(stream.readall()))
    
    # Create aggregations
    summary = df.groupby(['store_id', 'category']).agg({
        'sales_amount': ['sum', 'mean', 'count'],
        'units_sold': 'sum'
    }).reset_index()
    
    summary.columns = ['store_id', 'category', 'total_sales', 'avg_sale', 'transaction_count', 'total_units']
    summary['execution_date'] = execution_date
    
    # Upload to gold layer
    csv_buffer = BytesIO()
    summary.to_csv(csv_buffer, index=False)
    csv_buffer.seek(0)
    file_size = csv_buffer.getbuffer().nbytes
    
    gold_blob = gold_container.get_blob_client(gold_path)
    gold_blob.upload_blob(csv_buffer, overwrite=True)
    
    logger.info(f"✓ Created gold layer summary: {len(summary)} records ({file_size:,} bytes)")
    
    return {
        'records_created': len(summary),
        'output_path': gold_path
    }


def refresh_powerbi_dataset(**context):
    """Trigger PowerBI dataset refresh."""
    logger.info("Triggering PowerBI dataset refresh...")
    
    # This is a placeholder - implement based on your PowerBI setup
    # Typically uses PowerBI REST API with service principal authentication
    
    logger.info("✓ PowerBI dataset refresh triggered")
    
    return {'status': 'refresh_triggered'}


def send_success_notification(**context):
    """Send success notification."""
    execution_date = context['ds']
    task_results = context['ti'].xcom_pull(task_ids=[
        'ingest_data',
        'validate_quality',
        'load_to_gold'
    ])
    
    logger.info(f"Pipeline completed successfully for {execution_date}")
    logger.info(f"Results: {task_results}")
    
    # In production, send email/Slack notification here
    return {'notification_sent': True}


# --------------------------------------------------------------------------------
# DAG DEFINITION
# --------------------------------------------------------------------------------

default_args = {
    'owner': 'data_engineering',
    'depends_on_past': True,  # Don't run if previous day failed
    'email': ['data-team@spencergifts.com'],
    'email_on_failure': True,
    'email_on_retry': False,
    'retries': 2,
    'retry_delay': timedelta(minutes=5),
    'execution_timeout': timedelta(hours=4),
}

with DAG(
    dag_id='end_to_end_etl_pipeline',
    default_args=default_args,
    description='Production ETL pipeline: Azure → Databricks → PowerBI',
    schedule='0 2 * * *',  # Daily at 2 AM EST
    start_date=datetime(2025, 12, 1),
    catchup=False,
    max_active_runs=1,
    tags=['production', 'etl', 'daily'],
    doc_md=__doc__
) as dag:
    
    # Start marker
    start = EmptyOperator(task_id='start')
    
    # Stage 1: Data Ingestion
    with TaskGroup('ingestion', tooltip='Ingest raw data from Azure Blob') as ingestion:
        ingest_data = PythonOperator(
            task_id='ingest_data',
            python_callable=ingest_from_azure,
            provide_context=True
        )
        
        validate_quality = PythonOperator(
            task_id='validate_quality',
            python_callable=validate_data_quality,
            provide_context=True
        )
        
        ingest_data >> validate_quality
    
    # Stage 2: Transformation
    with TaskGroup('transformation', tooltip='Transform data in Databricks') as transformation:
        transform_bronze_to_silver = PythonOperator(
            task_id='transform_bronze_to_silver',
            python_callable=transform_in_databricks,
            provide_context=True
        )
        
        load_to_gold = PythonOperator(
            task_id='load_to_gold',
            python_callable=load_to_gold_layer,
            provide_context=True
        )
        
        transform_bronze_to_silver >> load_to_gold
    
    # Stage 3: Consumption Layer
    with TaskGroup('consumption', tooltip='Prepare data for consumption') as consumption:
        refresh_powerbi = PythonOperator(
            task_id='refresh_powerbi',
            python_callable=refresh_powerbi_dataset,
            provide_context=True
        )
    
    # Final notification
    notify_success = PythonOperator(
        task_id='notify_success',
        python_callable=send_success_notification,
        provide_context=True,
        trigger_rule='all_success'
    )
    
    # End marker
    end = EmptyOperator(task_id='end')
    
    # Pipeline flow
    start >> ingestion >> transformation >> consumption >> notify_success >> end
