"""Azure Blob Copy Operations DAG
==============================
Demonstrates copying files between containers.

Examples:
- Copy single file between containers
- Copy multiple files (pattern-based)
"""

from airflow import DAG
from airflow.operators.python import PythonOperator
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)


def copy_blob_within_account(**context):
    """Copy a single blob from one container to another in same storage account."""
    from src.connectors import get_azure_storage_connector
    import os
    
    # Get connector
    azure = get_azure_storage_connector('azure_default')
    
    # Configuration - you can change these
    source_container = context.get('params', {}).get('source_container', 'staging')
    target_container = context.get('params', {}).get('target_container', 'processed')
    blob_name = context.get('params', {}).get('blob_name', 'test/sample_file.csv')
    
    logger.info(f"Copying {blob_name} from {source_container} to {target_container}")
    
    # Create temp file path
    temp_file = f'/tmp/temp_copy_{os.path.basename(blob_name)}'
    
    try:
        # Download from source
        logger.info(f"Step 1: Downloading from {source_container}/{blob_name}")
        azure.download_file(source_container, blob_name, temp_file)
        
        # Upload to target
        logger.info(f"Step 2: Uploading to {target_container}/{blob_name}")
        azure.upload_file(temp_file, target_container, blob_name)
        
        logger.info("✓ Copy completed successfully")
        
        # Cleanup temp file
        if os.path.exists(temp_file):
            os.remove(temp_file)
            logger.info(f"✓ Cleaned up temp file: {temp_file}")
        
        return {
            'status': 'success',
            'source': f"{source_container}/{blob_name}",
            'target': f"{target_container}/{blob_name}"
        }
    except Exception as e:
        logger.error(f"✗ Copy failed: {str(e)}")
        # Cleanup temp file on error
        if os.path.exists(temp_file):
            os.remove(temp_file)
        raise


def copy_multiple_blobs_by_prefix(**context):
    """Copy all blobs matching a prefix between containers."""
    from src.connectors import get_azure_storage_connector
    import os
    
    azure = get_azure_storage_connector('azure_default')
    
    # Configuration - you can change these
    source_container = context.get('params', {}).get('source_container', 'staging')
    target_container = context.get('params', {}).get('target_container', 'archive')
    prefix = context.get('params', {}).get('prefix', 'sales/2024-12/')
    
    logger.info(f"Copying all blobs with prefix '{prefix}' from {source_container} to {target_container}")
    
    try:
        # List blobs matching prefix
        blobs = azure.list_blobs(source_container, prefix=prefix)
        logger.info(f"Found {len(blobs)} blobs to copy")
        
        if len(blobs) == 0:
            logger.warning(f"No blobs found with prefix '{prefix}' in {source_container}")
            return {'status': 'no_files', 'copied_count': 0, 'blobs': []}
        
        copied = []
        for blob_name in blobs:
            temp_file = f'/tmp/batch_copy_{blob_name.replace("/", "_")}'
            
            try:
                # Download
                logger.info(f"Downloading {blob_name}...")
                azure.download_file(source_container, blob_name, temp_file)
                
                # Upload to target
                logger.info(f"Uploading to {target_container}/{blob_name}...")
                azure.upload_file(temp_file, target_container, blob_name)
                
                copied.append(blob_name)
                logger.info(f"✓ Copied {blob_name}")
                
                # Cleanup temp file
                if os.path.exists(temp_file):
                    os.remove(temp_file)
            except Exception as e:
                logger.error(f"✗ Failed to copy {blob_name}: {str(e)}")
                # Cleanup temp file on error
                if os.path.exists(temp_file):
                    os.remove(temp_file)
                # Continue with next file
                continue
        
        logger.info(f"✓ Successfully copied {len(copied)} out of {len(blobs)} blobs")
        return {
            'status': 'success',
            'copied_count': len(copied),
            'total_count': len(blobs),
            'blobs': copied
        }
    except Exception as e:
        logger.error(f"✗ Batch copy failed: {str(e)}")
        raise





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
    schedule=None,  # Manual trigger only
    catchup=False,
    tags=['azure', 'blob', 'copy', 'example'],
    params={
        'source_container': 'sg-analytics-raw',
        'target_container': 'airflow',
        'blob_name': 'seasonal_buy/2025-10-13/'
    }
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
    
    # Tasks run independently (no dependencies)
    [copy_single, copy_batch]
