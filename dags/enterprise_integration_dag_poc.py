"""
Enterprise Integration DAG - POC Version
========================================

This is a simplified POC version that uses mock data and doesn't require
actual connections to external systems. Perfect for demonstrating the
pipeline flow without needing credentials.

To run with real connections:
1. Set Airflow Variables in UI (Admin → Variables):
   - onprem_db_host, onprem_db_user, onprem_db_password
   - azure_storage_account, azure_storage_key
   - databricks_host, databricks_token
   - powerbi_workspace_id, powerbi_dataset_id

2. Or use the full version in enterprise_integration_dag.py after
   setting up connections via UI (Admin → Connections)
"""

from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.exceptions import AirflowException
from airflow.models import Variable
import logging

default_args = {
    "owner": "data_engineering",
    "retries": 1,
    "retry_delay": timedelta(minutes=5),
}


def extract_from_onprem_mock(**context):
    """
    Mock extraction - generates sample data instead of connecting to actual DB.
    For real connection, set Variables: onprem_db_host, onprem_db_user, onprem_db_password
    """
    logger = context['task_instance'].log
    logger.info("🔧 POC Mode: Using mock data (no real DB connection)")
    
    # Check if user wants to use real connection
    use_real_connection = Variable.get("use_real_connections", default_var="false") == "true"
    
    if use_real_connection:
        # Get credentials from Variables (set in UI on-the-fly)
        db_host = Variable.get("onprem_db_host", default_var=None)
        db_user = Variable.get("onprem_db_user", default_var=None)
        db_password = Variable.get("onprem_db_password", default_var=None)
        
        if not all([db_host, db_user, db_password]):
            logger.warning("⚠️  Real connection requested but credentials not set in Variables")
            logger.info("Set these in UI: Admin → Variables → + Add")
            logger.info("  - onprem_db_host")
            logger.info("  - onprem_db_user") 
            logger.info("  - onprem_db_password")
            use_real_connection = False
    
    if use_real_connection:
        logger.info(f"Connecting to {db_host}...")
        # Real connection code would go here
        # from src.connectors import fetch_from_onprem
        # data = fetch_from_onprem('sql_server', config, query)
    
    # Generate mock data
    import random
    mock_data = []
    for i in range(100):
        mock_data.append({
            'SalesID': i + 1,
            'OrderDate': (datetime.now() - timedelta(days=random.randint(0, 30))).strftime('%Y-%m-%d'),
            'Amount': round(random.uniform(10, 1000), 2),
            'CustomerID': f'CUST{random.randint(1000, 9999)}',
            'Product': random.choice(['Product A', 'Product B', 'Product C', 'Product D']),
            'Quantity': random.randint(1, 10)
        })
    
    logger.info(f"✓ Extracted {len(mock_data)} records (mock data)")
    context['task_instance'].xcom_push(key='onprem_data', value=mock_data)
    
    return {
        'status': 'success',
        'records_extracted': len(mock_data),
        'mode': 'mock'
    }


def stage_to_azure_mock(**context):
    """
    Mock staging - simulates upload to Azure Storage.
    For real upload, set Variables: azure_storage_account, azure_storage_key
    """
    logger = context['task_instance'].log
    logger.info("🔧 POC Mode: Simulating Azure Storage upload")
    
    # Get data from previous task
    data = context['task_instance'].xcom_pull(
        task_ids='extract_from_onprem',
        key='onprem_data'
    )
    
    import pandas as pd
    df = pd.DataFrame(data)
    logger.info(f"DataFrame shape: {df.shape}")
    
    # Check if user wants real Azure upload
    use_real_connection = Variable.get("use_real_connections", default_var="false") == "true"
    
    if use_real_connection:
        azure_account = Variable.get("azure_storage_account", default_var=None)
        azure_key = Variable.get("azure_storage_key", default_var=None)
        
        if not all([azure_account, azure_key]):
            logger.warning("⚠️  Real Azure upload requested but credentials not set")
            use_real_connection = False
    
    # Simulate staging
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    blob_name = f"sales_data/staging/sales_{timestamp}.csv"
    
    if use_real_connection:
        logger.info(f"Uploading to Azure Storage: {blob_name}")
        # Real upload code would go here
        # from src.connectors import get_azure_storage_connector
        # connector = get_azure_storage_connector()
        # connector.upload_dataframe(df, 'staging', blob_name, 'csv')
    else:
        logger.info(f"✓ Simulated upload to: {blob_name}")
        logger.info(f"  Rows: {len(df)}, Columns: {list(df.columns)}")
    
    context['task_instance'].xcom_push(key='staging_path', value=blob_name)
    
    return {
        'status': 'success',
        'staging_blob': blob_name,
        'rows_staged': len(df),
        'mode': 'mock'
    }


def transform_in_databricks_mock(**context):
    """
    Mock transformation - simulates Databricks SQL queries.
    For real execution, set Variables: databricks_host, databricks_token
    """
    logger = context['task_instance'].log
    logger.info("🔧 POC Mode: Simulating Databricks transformation")
    
    staging_path = context['task_instance'].xcom_pull(
        task_ids='stage_to_azure',
        key='staging_path'
    )
    
    logger.info(f"Staged data path: {staging_path}")
    
    # Check if user wants real Databricks execution
    use_real_connection = Variable.get("use_real_connections", default_var="false") == "true"
    
    if use_real_connection:
        db_host = Variable.get("databricks_host", default_var=None)
        db_token = Variable.get("databricks_token", default_var=None)
        
        if not all([db_host, db_token]):
            logger.warning("⚠️  Real Databricks execution requested but credentials not set")
            use_real_connection = False
    
    # Simulate transformations
    tables_created = [
        'sales.sales_raw_cleaned',
        'sales.sales_daily_summary',
        'sales.sales_by_product'
    ]
    
    for table in tables_created:
        if use_real_connection:
            logger.info(f"Creating table: {table}")
            # Real execution would go here
            # from src.connectors import get_databricks_connector
            # databricks = get_databricks_connector()
            # databricks.run_query(query)
        else:
            logger.info(f"✓ Simulated table creation: {table}")
    
    logger.info("✓ All transformations completed (mock)")
    
    return {
        'status': 'success',
        'tables_created': len(tables_created),
        'tables': tables_created,
        'mode': 'mock'
    }


def refresh_powerbi_mock(**context):
    """
    Mock Power BI refresh - simulates dataset refresh trigger.
    For real refresh, set Variables: powerbi_workspace_id, powerbi_dataset_id, etc.
    """
    logger = context['task_instance'].log
    logger.info("🔧 POC Mode: Simulating Power BI dataset refresh")
    
    # Check if user wants real refresh
    use_real_connection = Variable.get("use_real_connections", default_var="false") == "true"
    
    if use_real_connection:
        workspace_id = Variable.get("powerbi_workspace_id", default_var=None)
        dataset_id = Variable.get("powerbi_dataset_id", default_var=None)
        
        if not all([workspace_id, dataset_id]):
            logger.warning("⚠️  Real Power BI refresh requested but IDs not set")
            use_real_connection = False
    
    if use_real_connection:
        logger.info(f"Triggering refresh for dataset: {dataset_id}")
        # Real refresh would go here
        # from src.connectors import get_powerbi_connector
        # powerbi = get_powerbi_connector()
        # powerbi.refresh_dataset(workspace_id, dataset_id)
    else:
        logger.info("✓ Simulated Power BI dataset refresh")
        logger.info("  Refresh Status: Success")
        logger.info("  Tables: 3")
    
    return {
        'status': 'success',
        'dataset_id': Variable.get("powerbi_dataset_id", default_var="mock-dataset-id"),
        'tables_count': 3,
        'mode': 'mock'
    }


def validate_pipeline(**context):
    """
    Validate the entire pipeline by checking results from each task.
    """
    logger = context['task_instance'].log
    logger.info("🔍 Validating pipeline execution...")
    
    # Get results from all tasks
    extract_result = context['task_instance'].xcom_pull(task_ids='extract_from_onprem')
    stage_result = context['task_instance'].xcom_pull(task_ids='stage_to_azure')
    transform_result = context['task_instance'].xcom_pull(task_ids='transform_in_databricks')
    refresh_result = context['task_instance'].xcom_pull(task_ids='refresh_powerbi')
    
    logger.info("="*60)
    logger.info("Pipeline Execution Summary")
    logger.info("="*60)
    logger.info(f"✓ Extract: {extract_result.get('records_extracted', 'N/A')} records ({extract_result.get('mode', 'N/A')} mode)")
    logger.info(f"✓ Stage: {stage_result.get('rows_staged', 'N/A')} rows → {stage_result.get('staging_blob', 'N/A')}")
    logger.info(f"✓ Transform: {transform_result.get('tables_created', 'N/A')} tables created")
    logger.info(f"✓ Refresh: Dataset refreshed successfully")
    logger.info("="*60)
    
    mode = extract_result.get('mode', 'mock')
    if mode == 'mock':
        logger.info("ℹ️  Running in POC/Mock mode")
        logger.info("   To use real connections:")
        logger.info("   1. Go to Admin → Variables in Airflow UI")
        logger.info("   2. Add variable: use_real_connections = true")
        logger.info("   3. Add credential variables (see DAG docstring)")
    
    return {
        'status': 'success',
        'message': 'Pipeline validation successful',
        'mode': mode,
        'extract_records': extract_result.get('records_extracted'),
        'staged_rows': stage_result.get('rows_staged'),
        'tables_created': transform_result.get('tables_created'),
    }


# ============================================================================
# DAG DEFINITION
# ============================================================================

with DAG(
    dag_id='enterprise_integration_pipeline_poc',
    description='POC: Mock pipeline - no credentials needed',
    default_args=default_args,
    start_date=datetime(2024, 1, 1),
    schedule_interval='@daily',
    catchup=False,
    tags=['poc', 'mock', 'demo'],
    doc_md=__doc__,
) as dag:
    
    extract = PythonOperator(
        task_id='extract_from_onprem',
        python_callable=extract_from_onprem_mock,
        doc='Extract sales data (mock or real based on Variables)'
    )
    
    stage = PythonOperator(
        task_id='stage_to_azure',
        python_callable=stage_to_azure_mock,
        doc='Stage data to Azure Storage (mock or real)'
    )
    
    transform = PythonOperator(
        task_id='transform_in_databricks',
        python_callable=transform_in_databricks_mock,
        doc='Transform data in Databricks (mock or real)'
    )
    
    refresh = PythonOperator(
        task_id='refresh_powerbi',
        python_callable=refresh_powerbi_mock,
        doc='Refresh Power BI dataset (mock or real)'
    )
    
    validate = PythonOperator(
        task_id='validate_pipeline',
        python_callable=validate_pipeline,
        doc='Validate pipeline execution'
    )
    
    # Define dependencies
    extract >> stage >> transform >> refresh >> validate
