"""Azure Blob Copy - Simple File Transfer
========================================
Easy-to-use DAG to copy files between Azure Blob Storage containers.

Just change these 3 things when you trigger:
    1. source_container - Where to copy FROM
    2. target_container - Where to copy TO  
    3. folder_path - Which folder/files to copy

Example:
    {
        "source_container": "raw-data",
        "target_container": "processed-data",
        "folder_path": "sales/2024-12/"
    }
"""

from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.providers.microsoft.azure.hooks.wasb import WasbHook
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)


def copy_files(**context):
    """Copy files from source container to target container."""
    
    # Get parameters
    source_container = context['params']['source_container']
    target_container = context['params']['target_container']
    folder_path = context['params']['folder_path']
    
    logger.info("=" * 60)
    logger.info(f"Copying files from {source_container} to {target_container}")
    logger.info(f"Folder: {folder_path}")
    logger.info("=" * 60)
    
    # Connect to Azure Storage
    hook = WasbHook(wasb_conn_id='azure_blob_default')
    
    # Find all files in the folder
    logger.info(f"Finding files in {source_container}/{folder_path}...")
    files = hook.get_blobs_list(container_name=source_container, prefix=folder_path)
    
    if not files:
        logger.warning(f"No files found in {folder_path}")
        return {'status': 'no_files', 'copied': 0}
    
    logger.info(f"Found {len(files)} files to copy")
    
    # Copy each file
    copied = 0
    failed = 0
    
    for file_name in files:
        try:
            logger.info(f"  Copying: {file_name}")
            
            # Read from source
            file_data = hook.read_file(container_name=source_container, blob_name=file_name)
            
            # Write to target (same path)
            hook.load_string(
                string_data=file_data,
                container_name=target_container,
                blob_name=file_name,
                overwrite=True
            )
            
            copied += 1
            logger.info(f"  ✓ Success")
            
        except Exception as e:
            failed += 1
            logger.error(f"  ✗ Failed: {str(e)}")
    
    logger.info("=" * 60)
    logger.info(f"Done! Copied {copied} files, {failed} failed")
    logger.info("=" * 60)
    
    return {
        'status': 'success',
        'total': len(files),
        'copied': copied,
        'failed': failed
    }


# DAG definition
default_args = {
    'owner': 'airflow',
    'depends_on_past': False,
    'start_date': datetime(2024, 12, 1),
    'email_on_failure': False,
    'email_on_retry': False,
    'retries': 2,
    'retry_delay': timedelta(minutes=2),
}

with DAG(
    'azure_blob_copy_generic',
    default_args=default_args,
    description='Simple DAG to copy files between Azure Blob Storage containers',
    schedule=None,
    catchup=False,
    tags=['azure', 'blob', 'copy'],
    params={
        'source_container': 'sg-analytics-raw',
        'target_container': 'airflow',
        'folder_path': 'seasonal_buy/2025-10-13/'
    }
) as dag:
    
    copy_task = PythonOperator(
        task_id='copy_files',
        python_callable=copy_files
    )
