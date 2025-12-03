"""
Azure Blob Copy Operations DAG
==============================
Demonstrates copying files between containers and storage accounts.

Examples:
- Copy single file between containers
- Copy multiple files (pattern-based)
- Copy between different storage accounts
"""

from airflow import DAG
from airflow.operators.python import PythonOperator
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)


def copy_blob_within_account(**context):
    """Copy a single blob from one container to another in same storage account."""
    from src.connectors import get_azure_storage_connector
    
    # Get connector
    azure = get_azure_storage_connector('azure_default')
    
    # Configuration
    source_container = 'staging'
    target_container = 'processed'
    blob_name = 'sales/daily_export.csv'
    
    logger.info(f"Copying {blob_name} from {source_container} to {target_container}")
    
    # Download from source
    temp_file = '/tmp/temp_copy.csv'
    azure.download_file(source_container, blob_name, temp_file)
    
    # Upload to target
    azure.upload_file(temp_file, target_container, blob_name)
    
    logger.info("✓ Copy completed")
    return {'source': f"{source_container}/{blob_name}", 'target': f"{target_container}/{blob_name}"}


def copy_multiple_blobs_by_prefix(**context):
    """Copy all blobs matching a prefix between containers."""
    from src.connectors import get_azure_storage_connector
    
    azure = get_azure_storage_connector('azure_default')
    
    # Configuration
    source_container = 'staging'
    target_container = 'archive'
    prefix = 'sales/2024-12/'
    
    logger.info(f"Copying all blobs with prefix '{prefix}'")
    
    # List blobs matching prefix
    blobs = azure.list_blobs(source_container, prefix=prefix)
    logger.info(f"Found {len(blobs)} blobs to copy")
    
    copied = []
    for blob_name in blobs:
        temp_file = f'/tmp/batch_copy_{blob_name.replace("/", "_")}'
        
        # Download
        azure.download_file(source_container, blob_name, temp_file)
        
        # Upload to target
        azure.upload_file(temp_file, target_container, blob_name)
        
        copied.append(blob_name)
        logger.info(f"✓ Copied {blob_name}")
    
    logger.info(f"✓ Copied {len(copied)} blobs")
    return {'copied_count': len(copied), 'blobs': copied}


def copy_between_storage_accounts(**context):
    """Copy blobs between different Azure Storage accounts."""
    from src.connectors import AzureStorageConnector
    
    # Source storage account
    source_azure = AzureStorageConnector(
        account_name='sourcestorageaccount',
        account_key='source_key_here'  # Better: use Airflow Variables
    )
    
    # Target storage account
    target_azure = AzureStorageConnector(
        account_name='targetstorageaccount',
        account_key='target_key_here'  # Better: use Airflow Variables
    )
    
    # Configuration
    source_container = 'exports'
    target_container = 'imports'
    blob_name = 'daily_sales.csv'
    
    logger.info(f"Cross-account copy: {blob_name}")
    
    # Download from source account
    temp_file = '/tmp/cross_account_copy.csv'
    source_azure.download_file(source_container, blob_name, temp_file)
    
    # Upload to target account
    target_azure.upload_file(temp_file, target_container, blob_name)
    
    logger.info("✓ Cross-account copy completed")
    return {'blob': blob_name, 'status': 'success'}


# DAG definition
default_args = {
    'owner': 'airflow',
    'depends_on_past': False,
    'start_date': datetime(2024, 12, 1),
    'email_on_failure': False,
    'email_on_retry': False,
    'retries': 1,
    'retry_delay': timedelta(minutes=5),
}

with DAG(
    'azure_blob_copy_operations',
    default_args=default_args,
    description='Copy files between Azure Blob containers and storage accounts',
    schedule_interval='@daily',
    catchup=False,
    tags=['azure', 'blob', 'copy', 'example'],
) as dag:
    
    # Task 1: Copy single blob within account
    copy_single = PythonOperator(
        task_id='copy_blob_within_account',
        python_callable=copy_blob_within_account,
    )
    
    # Task 2: Copy multiple blobs by prefix
    copy_batch = PythonOperator(
        task_id='copy_multiple_blobs_by_prefix',
        python_callable=copy_multiple_blobs_by_prefix,
    )
    
    # Task 3: Copy between storage accounts
    copy_cross_account = PythonOperator(
        task_id='copy_between_storage_accounts',
        python_callable=copy_between_storage_accounts,
    )
    
    # Tasks run independently (no dependencies)
    [copy_single, copy_batch, copy_cross_account]
