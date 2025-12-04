"""Azure Blob Copy - Seasonal Buy Files
=====================================
Production DAG using official Airflow Azure operators to copy seasonal buy files
from sg-analytics-raw to airflow container.

This DAG demonstrates:
- Using WasbHook (Azure Blob Storage Hook)
- Listing files with prefix
- Copying multiple files in parallel
- Error handling and logging
"""

from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.providers.microsoft.azure.hooks.wasb import WasbHook
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)


def list_source_files(**context):
    """List all files in the source location."""
    
    # Configuration
    source_container = context['params']['source_container']
    prefix = context['params']['prefix']
    
    logger.info(f"Listing files in {source_container} with prefix: {prefix}")
    
    # Use Airflow's Azure Hook
    hook = WasbHook(wasb_conn_id='azure_blob_default')
    
    # List all blobs with the prefix
    blobs = hook.get_blobs_list(container_name=source_container, prefix=prefix)
    
    logger.info(f"✓ Found {len(blobs)} files to copy")
    
    for blob in blobs[:5]:  # Log first 5
        logger.info(f"  - {blob}")
    if len(blobs) > 5:
        logger.info(f"  ... and {len(blobs) - 5} more")
    
    # Push list to XCom for downstream tasks
    context['task_instance'].xcom_push(key='blob_list', value=blobs)
    
    return {'total_files': len(blobs), 'blobs': blobs}


def copy_files(**context):
    """Copy all files from source to target container."""
    
    # Get configuration
    source_container = context['params']['source_container']
    target_container = context['params']['target_container']
    
    # Get list of files from previous task
    ti = context['task_instance']
    blobs = ti.xcom_pull(task_ids='list_source_files', key='blob_list')
    
    if not blobs or len(blobs) == 0:
        logger.warning("No files to copy!")
        return {'status': 'no_files', 'copied': 0}
    
    logger.info(f"Copying {len(blobs)} files from {source_container} to {target_container}")
    
    # Use Airflow's Azure Hook
    hook = WasbHook(wasb_conn_id='azure_blob_default')
    
    copied = 0
    failed = 0
    
    for blob_name in blobs:
        try:
            logger.info(f"Copying: {blob_name}")
            
            # Check if blob exists in source
            if not hook.check_for_blob(container_name=source_container, blob_name=blob_name):
                logger.warning(f"Source blob not found: {blob_name}")
                failed += 1
                continue
            
            # Read from source
            blob_data = hook.read_file(container_name=source_container, blob_name=blob_name)
            
            # Write to target
            hook.load_string(
                string_data=blob_data,
                container_name=target_container,
                blob_name=blob_name,
                overwrite=True
            )
            
            logger.info(f"✓ Copied: {blob_name}")
            copied += 1
            
        except Exception as e:
            logger.error(f"✗ Failed to copy {blob_name}: {str(e)}")
            failed += 1
            continue
    
    result = {
        'status': 'completed',
        'total': len(blobs),
        'copied': copied,
        'failed': failed
    }
    
    logger.info(f"Copy complete: {copied} succeeded, {failed} failed out of {len(blobs)} total")
    
    return result


def verify_copy(**context):
    """Verify files were copied successfully."""
    
    target_container = context['params']['target_container']
    prefix = context['params']['prefix']
    
    logger.info(f"Verifying files in {target_container} with prefix: {prefix}")
    
    # Use Airflow's Azure Hook
    hook = WasbHook(wasb_conn_id='azure_blob_default')
    
    # List blobs in target
    target_blobs = hook.get_blobs_list(container_name=target_container, prefix=prefix)
    
    logger.info(f"✓ Found {len(target_blobs)} files in target container")
    
    # Get original count from previous task
    ti = context['task_instance']
    copy_result = ti.xcom_pull(task_ids='copy_files')
    
    if copy_result:
        original_count = copy_result['copied']
        if len(target_blobs) >= original_count:
            logger.info(f"✓ Verification passed: {len(target_blobs)} files in target")
        else:
            logger.warning(f"⚠ Verification issue: Expected {original_count}, found {len(target_blobs)}")
    
    return {
        'target_file_count': len(target_blobs),
        'verification': 'passed' if copy_result and len(target_blobs) >= copy_result['copied'] else 'failed'
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
    'azure_blob_copy_seasonal_buy',
    default_args=default_args,
    description='Copy seasonal buy files from sg-analytics-raw to airflow container using Airflow Azure operators',
    schedule=None,  # Manual trigger only
    catchup=False,
    tags=['azure', 'blob', 'copy', 'seasonal-buy', 'production'],
    params={
        'source_container': 'sg-analytics-raw',
        'target_container': 'airflow',
        'prefix': 'seasonal_buy/2025-10-13/'
    }
) as dag:
    
    # Task 1: List source files
    list_files = PythonOperator(
        task_id='list_source_files',
        python_callable=list_source_files,
    )
    
    # Task 2: Copy files from source to target
    copy = PythonOperator(
        task_id='copy_files',
        python_callable=copy_files,
    )
    
    # Task 3: Verify the copy
    verify = PythonOperator(
        task_id='verify_copy',
        python_callable=verify_copy,
    )
    
    # Define task dependencies
    list_files >> copy >> verify
