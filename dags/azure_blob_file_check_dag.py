"""
"""Azure Blob File Check DAG
=========================
Demonstrates checking for file existence.

Examples:
- Check if single file exists
- Check if multiple files exist
"""

from airflow import DAG
from airflow.operators.python import PythonOperator
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)


def check_blob_exists(**context):
    """Check if a specific blob exists."""
    from src.connectors import get_azure_storage_connector
    
    azure = get_azure_storage_connector('azure_default')
    
    container = 'staging'
    blob_name = 'sales/daily_export.csv'
    
    logger.info(f"Checking if {container}/{blob_name} exists...")
    
    # List all blobs and check if our file is present
    blobs = azure.list_blobs(container, prefix='sales/')
    exists = blob_name in blobs
    
    if exists:
        logger.info(f"✓ File exists: {blob_name}")
    else:
        logger.warning(f"✗ File not found: {blob_name}")
    
    # Push result to XCom for downstream tasks
    context['task_instance'].xcom_push(key='file_exists', value=exists)
    context['task_instance'].xcom_push(key='blob_name', value=blob_name)
    
    return exists





def wait_for_multiple_files(**context):
    """Wait for multiple files to be present before proceeding."""
    from src.connectors import get_azure_storage_connector
    
    azure = get_azure_storage_connector('azure_default')
    
    container = 'staging'
    required_files = [
        'sales/customer_data.csv',
        'sales/product_data.csv',
        'sales/transaction_data.csv'
    ]
    
    logger.info(f"Checking for {len(required_files)} required files...")
    
    # List all blobs
    all_blobs = azure.list_blobs(container, prefix='sales/')
    
    # Check each required file
    missing = []
    found = []
    for file in required_files:
        if file in all_blobs:
            found.append(file)
            logger.info(f"✓ Found: {file}")
        else:
            missing.append(file)
            logger.warning(f"✗ Missing: {file}")
    
    all_present = len(missing) == 0
    
    if all_present:
        logger.info("✓ All required files present")
    else:
        logger.warning(f"✗ Missing {len(missing)} files: {missing}")
    
    return {
        'all_present': all_present,
        'found': found,
        'missing': missing,
        'found_count': len(found),
        'missing_count': len(missing)
    }





# DAG definition
default_args = {
    'owner': 'airflow',
    'depends_on_past': False,
    'start_date': datetime(2024, 12, 1),
    'email_on_failure': False,
    'email_on_retry': False,
    'retries': 2,
    'retry_delay': timedelta(minutes=5),
}

with DAG(
    'azure_blob_file_check',
    default_args=default_args,
    description='Check for file existence in Azure Blob Storage',
    schedule='@hourly',
    catchup=False,
    tags=['azure', 'blob', 'file-check', 'example'],
) as dag:
    
    # Task 1: Check if blob exists
    check_file = PythonOperator(
        task_id='check_blob_exists',
        python_callable=check_blob_exists,
    )
    
    # Task 2: Wait for multiple files
    wait_multiple = PythonOperator(
        task_id='wait_for_multiple_files',
        python_callable=wait_for_multiple_files,
    )
    
    # Tasks run independently
    [check_file, wait_multiple]
