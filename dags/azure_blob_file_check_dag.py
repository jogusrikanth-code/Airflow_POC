"""
Azure Blob File Check DAG
=========================
Demonstrates checking for file existence and conditional processing.

Examples:
- Check if file exists before processing
- Wait for multiple files to arrive
- Validate file presence in blob storage
"""

from airflow import DAG
from airflow.operators.python import PythonOperator, BranchPythonOperator
from airflow.operators.empty import EmptyOperator
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


def branch_on_file_exists(**context):
    """Branch based on whether file exists."""
    ti = context['task_instance']
    file_exists = ti.xcom_pull(task_ids='check_blob_exists', key='file_exists')
    
    if file_exists:
        logger.info("File exists - proceeding to process")
        return 'process_file'
    else:
        logger.info("File not found - skipping processing")
        return 'file_not_found'


def process_file(**context):
    """Process the file if it exists."""
    from src.connectors import get_azure_storage_connector
    
    ti = context['task_instance']
    blob_name = ti.xcom_pull(task_ids='check_blob_exists', key='blob_name')
    
    azure = get_azure_storage_connector('azure_default')
    
    logger.info(f"Processing {blob_name}...")
    
    # Download and process
    temp_file = '/tmp/process_file.csv'
    azure.download_file('staging', blob_name, temp_file)
    
    # Process file (example: read with pandas)
    import pandas as pd
    df = pd.read_csv(temp_file)
    logger.info(f"✓ Processed {len(df)} rows from {blob_name}")
    
    return {'rows': len(df), 'status': 'processed'}


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


def check_blob_by_pattern(**context):
    """Check for files matching a pattern (e.g., today's date)."""
    from src.connectors import get_azure_storage_connector
    from datetime import datetime
    
    azure = get_azure_storage_connector('azure_default')
    
    container = 'staging'
    today = datetime.now().strftime('%Y-%m-%d')
    pattern = f'sales/{today}_'
    
    logger.info(f"Looking for files matching pattern: {pattern}")
    
    # List blobs with prefix
    matching_blobs = azure.list_blobs(container, prefix=pattern)
    
    logger.info(f"✓ Found {len(matching_blobs)} files matching pattern")
    
    return {
        'pattern': pattern,
        'count': len(matching_blobs),
        'files': matching_blobs
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
    schedule_interval='@hourly',
    catchup=False,
    tags=['azure', 'blob', 'file-check', 'example'],
) as dag:
    
    # Task 1: Check if blob exists
    check_file = PythonOperator(
        task_id='check_blob_exists',
        python_callable=check_blob_exists,
    )
    
    # Task 2: Branch based on file existence
    branch_task = BranchPythonOperator(
        task_id='branch_on_file_exists',
        python_callable=branch_on_file_exists,
    )
    
    # Task 3a: Process file if exists
    process = PythonOperator(
        task_id='process_file',
        python_callable=process_file,
    )
    
    # Task 3b: File not found handler
    file_not_found = EmptyOperator(
        task_id='file_not_found',
    )
    
    # Task 4: Wait for multiple files (independent check)
    wait_multiple = PythonOperator(
        task_id='wait_for_multiple_files',
        python_callable=wait_for_multiple_files,
    )
    
    # Task 5: Check by pattern (independent check)
    check_pattern = PythonOperator(
        task_id='check_blob_by_pattern',
        python_callable=check_blob_by_pattern,
    )
    
    # Define task dependencies
    check_file >> branch_task >> [process, file_not_found]
    [wait_multiple, check_pattern]  # Independent tasks
