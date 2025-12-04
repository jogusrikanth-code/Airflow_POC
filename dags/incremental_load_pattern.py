"""
Incremental Load Pattern DAG
=============================
Demonstrates enterprise pattern for incremental data loading:
- Track last successful load timestamp
- Process only new/changed records
- Handle late-arriving data
- Maintain audit trail

Use Case: Loading transactional data from on-prem SQL Server to Azure Data Lake

Schedule: Every 15 minutes during business hours
"""

from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.models import Variable
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)


# --------------------------------------------------------------------------------
# HELPER FUNCTIONS
# --------------------------------------------------------------------------------

def get_last_load_timestamp(source_table):
    """Get the last successful load timestamp from Airflow Variables."""
    key = f"last_load_{source_table}"
    last_timestamp = Variable.get(key, default_var="2025-01-01 00:00:00")
    logger.info(f"Last load timestamp for {source_table}: {last_timestamp}")
    return last_timestamp


def set_last_load_timestamp(source_table, timestamp):
    """Store the last successful load timestamp."""
    key = f"last_load_{source_table}"
    Variable.set(key, timestamp)
    logger.info(f"Updated last load timestamp for {source_table}: {timestamp}")


# --------------------------------------------------------------------------------
# TASK FUNCTIONS
# --------------------------------------------------------------------------------

def extract_incremental_data(**context):
    """Extract only new/changed records from source system."""
    from airflow.providers.microsoft.mssql.hooks.mssql import MsSqlHook
    import pandas as pd
    
    source_table = context['params']['source_table']
    timestamp_column = context['params']['timestamp_column']
    
    logger.info(f"Extracting incremental data from {source_table}")
    
    # Get last load timestamp
    last_timestamp = get_last_load_timestamp(source_table)
    current_timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    # Connect to on-prem SQL Server using MsSqlHook
    hook = MsSqlHook(mssql_conn_id='onprem_sqlserver')
    conn = hook.get_sqlalchemy_engine()
    
    # Query for new/changed records
    query = f"""
        SELECT *
        FROM {source_table}
        WHERE {timestamp_column} > '{last_timestamp}'
          AND {timestamp_column} <= '{current_timestamp}'
        ORDER BY {timestamp_column}
    """
    
    logger.info(f"Query: {query}")
    
    # Execute query
    df = pd.read_sql(query, conn)
    record_count = len(df)
    
    logger.info(f"Extracted {record_count} new/changed records")
    
    if record_count == 0:
        logger.info("No new data to process - skipping downstream tasks")
        return {
            'record_count': 0,
            'status': 'no_data',
            'timestamp_range': {'start': last_timestamp, 'end': current_timestamp}
        }
    
    # Save to temporary location
    temp_file = f"/tmp/incremental_{source_table}_{context['ts_nodash']}.parquet"
    df.to_parquet(temp_file, index=False)
    
    logger.info(f"Saved extracted data to: {temp_file}")
    
    return {
        'record_count': record_count,
        'temp_file': temp_file,
        'timestamp_range': {'start': last_timestamp, 'end': current_timestamp},
        'status': 'data_extracted'
    }


def transform_incremental_data(**context):
    """Apply transformations to incremental data."""
    import pandas as pd
    
    # Get extraction results
    extract_result = context['ti'].xcom_pull(task_ids='extract_data')
    
    if extract_result['status'] == 'no_data':
        logger.info("No data to transform - skipping")
        return {'status': 'skipped', 'record_count': 0}
    
    temp_file = extract_result['temp_file']
    logger.info(f"Transforming data from: {temp_file}")
    
    # Load data
    df = pd.read_parquet(temp_file)
    
    # Apply transformations
    logger.info("Applying transformations...")
    
    # Example transformations:
    # 1. Standardize column names
    df.columns = df.columns.str.lower().str.replace(' ', '_')
    
    # 2. Handle nulls
    df = df.fillna({
        'store_id': 'UNKNOWN',
        'category': 'UNCATEGORIZED',
        'sales_amount': 0
    })
    
    # 3. Add metadata columns
    df['load_timestamp'] = datetime.now()
    df['source_system'] = 'on_prem_sql'
    df['load_id'] = context['run_id']
    
    # 4. Data type conversions
    if 'sales_amount' in df.columns:
        df['sales_amount'] = pd.to_numeric(df['sales_amount'], errors='coerce')
    
    if 'transaction_date' in df.columns:
        df['transaction_date'] = pd.to_datetime(df['transaction_date'], errors='coerce')
    
    # Save transformed data
    output_file = temp_file.replace('.parquet', '_transformed.parquet')
    df.to_parquet(output_file, index=False)
    
    logger.info(f"✓ Transformed {len(df)} records")
    logger.info(f"Saved to: {output_file}")
    
    return {
        'status': 'transformed',
        'record_count': len(df),
        'output_file': output_file
    }


def load_to_data_lake(**context):
    """Load transformed data to Azure Data Lake."""
    from airflow.providers.microsoft.azure.hooks.wasb import WasbHook
    import os
    
    # Get transformation results
    transform_result = context['ti'].xcom_pull(task_ids='transform_data')
    
    if transform_result['status'] == 'skipped':
        logger.info("No data to load - skipping")
        return {'status': 'skipped'}
    
    output_file = transform_result['output_file']
    source_table = context['params']['source_table']
    
    logger.info(f"Loading data to Azure Data Lake: {output_file}")
    
    # Get Azure Blob Hook
    hook = WasbHook(wasb_conn_id='azure_blob_default')
    client = hook.get_conn()
    
    # Define target path with partitioning
    execution_date = context['ds']
    target_container = "sg-analytics-bronze"
    target_path = f"incremental/{source_table}/date={execution_date}/data_{context['ts_nodash']}.parquet"
    
    # Upload file
    container = client.get_container_client(target_container)
    blob = container.get_blob_client(target_path)
    
    with open(output_file, 'rb') as data:
        blob.upload_blob(data, overwrite=True)
    
    file_size = os.path.getsize(output_file)
    
    logger.info(f"✓ Uploaded {file_size:,} bytes to {target_container}/{target_path}")
    
    # Clean up temp files
    os.remove(output_file)
    original_file = output_file.replace('_transformed.parquet', '.parquet')
    if os.path.exists(original_file):
        os.remove(original_file)
    
    return {
        'status': 'loaded',
        'target_path': target_path,
        'file_size': file_size,
        'record_count': transform_result['record_count']
    }


def update_audit_log(**context):
    """Update audit log and watermark for incremental loads."""
    from airflow.providers.microsoft.azure.hooks.wasb import WasbHook
    import pandas as pd
    from io import BytesIO
    
    source_table = context['params']['source_table']
    
    # Get results from all tasks
    extract_result = context['ti'].xcom_pull(task_ids='extract_data')
    load_result = context['ti'].xcom_pull(task_ids='load_to_data_lake')
    
    if extract_result['status'] == 'no_data':
        logger.info("No audit entry needed - no data processed")
        return {'status': 'skipped'}
    
    logger.info("Updating audit log...")
    
    # Create audit record
    audit_record = {
        'load_id': context['run_id'],
        'source_table': source_table,
        'execution_date': context['ds'],
        'timestamp_range_start': extract_result['timestamp_range']['start'],
        'timestamp_range_end': extract_result['timestamp_range']['end'],
        'records_extracted': extract_result['record_count'],
        'records_loaded': load_result['record_count'],
        'target_path': load_result['target_path'],
        'file_size_bytes': load_result['file_size'],
        'load_timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'status': 'SUCCESS'
    }
    
    # Get Azure Blob Hook
    hook = WasbHook(wasb_conn_id='azure_blob_default')
    client = hook.get_conn()
    
    # Append to audit log
    container = client.get_container_client("sg-analytics-bronze")
    audit_path = f"_audit_logs/incremental_loads/{source_table}.csv"
    
    # Download existing audit log (if exists)
    try:
        blob = container.get_blob_client(audit_path)
        existing_data = blob.download_blob().readall()
        existing_df = pd.read_csv(BytesIO(existing_data))
        audit_df = pd.concat([existing_df, pd.DataFrame([audit_record])], ignore_index=True)
    except Exception:
        # First audit record
        audit_df = pd.DataFrame([audit_record])
    
    # Upload updated audit log
    csv_buffer = BytesIO()
    audit_df.to_csv(csv_buffer, index=False)
    csv_buffer.seek(0)
    
    blob = container.get_blob_client(audit_path)
    blob.upload_blob(csv_buffer, overwrite=True)
    
    logger.info(f"✓ Audit log updated: {len(audit_df)} total entries")
    
    # Update watermark (last successful load timestamp)
    set_last_load_timestamp(
        source_table,
        extract_result['timestamp_range']['end']
    )
    
    logger.info("✓ Watermark updated successfully")
    
    return {
        'status': 'audit_completed',
        'total_audit_entries': len(audit_df)
    }


# --------------------------------------------------------------------------------
# DAG DEFINITION
# --------------------------------------------------------------------------------

default_args = {
    'owner': 'data_engineering',
    'depends_on_past': False,
    'email': ['data-team@spencergifts.com'],
    'email_on_failure': True,
    'retries': 3,
    'retry_delay': timedelta(minutes=2),
    'execution_timeout': timedelta(minutes=30),
}

with DAG(
    dag_id='incremental_load_pattern',
    default_args=default_args,
    description='Incremental data load from on-prem SQL Server to Azure Data Lake',
    schedule='*/15 6-22 * * *',  # Every 15 min, 6 AM - 10 PM EST
    start_date=datetime(2025, 12, 1),
    catchup=False,
    max_active_runs=1,
    tags=['incremental', 'sql-server', 'pattern'],
    doc_md=__doc__,
    params={
        'source_table': 'dbo.SalesTransactions',
        'timestamp_column': 'ModifiedDate'
    }
) as dag:
    
    extract_data = PythonOperator(
        task_id='extract_data',
        python_callable=extract_incremental_data,
        provide_context=True
    )
    
    transform_data = PythonOperator(
        task_id='transform_data',
        python_callable=transform_incremental_data,
        provide_context=True
    )
    
    load_to_data_lake_task = PythonOperator(
        task_id='load_to_data_lake',
        python_callable=load_to_data_lake,
        provide_context=True
    )
    
    update_audit = PythonOperator(
        task_id='update_audit',
        python_callable=update_audit_log,
        provide_context=True
    )
    
    # Pipeline flow
    extract_data >> transform_data >> load_to_data_lake_task >> update_audit
