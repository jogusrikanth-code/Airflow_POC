"""Azure Blob Copy - Generic File Transfer
========================================
Simple, reusable DAG to copy files between Azure Blob Storage locations.

Usage:
    Trigger with parameters to customize source/target and file patterns.
    
Examples:
    Copy specific file:
        {
            "source_container": "raw-data",
            "target_container": "processed-data",
            "source_path": "sales/2024/data.csv",
            "target_path": "archive/sales/2024/data.csv"
        }
    
    Copy all files in a folder:
        {
            "source_container": "raw-data",
            "target_container": "processed-data",
            "file_pattern": "sales/2024/*.csv"
        }
    
    Copy with prefix matching:
        {
            "source_container": "staging",
            "target_container": "production",
            "prefix": "reports/daily/"
        }
"""

from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.providers.microsoft.azure.hooks.wasb import WasbHook
from datetime import datetime, timedelta
import logging
import fnmatch

logger = logging.getLogger(__name__)


def copy_azure_blobs(**context):
    """
    Copy files from source to target container in Azure Blob Storage.
    
    Parameters (via DAG params or trigger config):
        source_container (str): Source container name
        target_container (str): Target container name
        source_path (str, optional): Specific file path to copy
        target_path (str, optional): Target file path (if copying single file)
        prefix (str, optional): Copy all files with this prefix
        file_pattern (str, optional): Pattern like "*.csv" or "data_*.txt"
    """
    
    params = context['params']
    
    # Get configuration
    source_container = params.get('source_container')
    target_container = params.get('target_container')
    source_path = params.get('source_path')
    target_path = params.get('target_path')
    prefix = params.get('prefix', '')
    file_pattern = params.get('file_pattern', '*')
    
    # Validate required parameters
    if not source_container or not target_container:
        raise ValueError("Both 'source_container' and 'target_container' are required!")
    
    logger.info("=" * 60)
    logger.info("Azure Blob Copy Configuration")
    logger.info("=" * 60)
    logger.info(f"Source Container: {source_container}")
    logger.info(f"Target Container: {target_container}")
    
    # Connect to Azure
    hook = WasbHook(wasb_conn_id='azure_blob_default')
    
    # Case 1: Copy specific single file
    if source_path:
        logger.info(f"Mode: Single file copy")
        logger.info(f"Source Path: {source_path}")
        
        # Use target_path if specified, otherwise same as source
        final_target_path = target_path if target_path else source_path
        logger.info(f"Target Path: {final_target_path}")
        
        return copy_single_file(hook, source_container, source_path, 
                               target_container, final_target_path)
    
    # Case 2: Copy multiple files with prefix/pattern
    else:
        logger.info(f"Mode: Multiple file copy")
        logger.info(f"Prefix: '{prefix}'")
        logger.info(f"File Pattern: '{file_pattern}'")
        
        return copy_multiple_files(hook, source_container, target_container, 
                                   prefix, file_pattern)


def copy_single_file(hook, source_container, source_path, target_container, target_path):
    """Copy a single file from source to target."""
    
    try:
        # Check if source exists
        if not hook.check_for_blob(container_name=source_container, blob_name=source_path):
            raise FileNotFoundError(f"Source file not found: {source_container}/{source_path}")
        
        logger.info(f"Reading from: {source_container}/{source_path}")
        
        # Read source file
        blob_data = hook.read_file(container_name=source_container, blob_name=source_path)
        
        # Write to target
        logger.info(f"Writing to: {target_container}/{target_path}")
        hook.load_string(
            string_data=blob_data,
            container_name=target_container,
            blob_name=target_path,
            overwrite=True
        )
        
        logger.info("✓ File copied successfully!")
        
        return {
            'status': 'success',
            'files_copied': 1,
            'source': f"{source_container}/{source_path}",
            'target': f"{target_container}/{target_path}"
        }
        
    except Exception as e:
        logger.error(f"✗ Copy failed: {str(e)}")
        raise


def copy_multiple_files(hook, source_container, target_container, prefix, file_pattern):
    """Copy multiple files matching prefix and pattern."""
    
    try:
        # List all blobs with prefix
        logger.info(f"Listing files in {source_container} with prefix '{prefix}'...")
        all_blobs = hook.get_blobs_list(container_name=source_container, prefix=prefix)
        
        if not all_blobs:
            logger.warning(f"No files found in {source_container} with prefix '{prefix}'")
            return {
                'status': 'no_files',
                'files_copied': 0,
                'files_failed': 0
            }
        
        # Filter by pattern if specified
        if file_pattern and file_pattern != '*':
            matching_blobs = [blob for blob in all_blobs if fnmatch.fnmatch(blob, file_pattern)]
            logger.info(f"Found {len(all_blobs)} files, {len(matching_blobs)} match pattern '{file_pattern}'")
        else:
            matching_blobs = all_blobs
            logger.info(f"Found {len(matching_blobs)} files to copy")
        
        if not matching_blobs:
            logger.warning(f"No files match pattern '{file_pattern}'")
            return {
                'status': 'no_matches',
                'files_copied': 0,
                'files_failed': 0
            }
        
        # Copy each file
        copied = 0
        failed = 0
        failed_files = []
        
        for blob_name in matching_blobs:
            try:
                logger.info(f"  Copying: {blob_name}")
                
                # Read from source
                blob_data = hook.read_file(container_name=source_container, blob_name=blob_name)
                
                # Write to target (same path)
                hook.load_string(
                    string_data=blob_data,
                    container_name=target_container,
                    blob_name=blob_name,
                    overwrite=True
                )
                
                copied += 1
                logger.info(f"  ✓ Copied: {blob_name}")
                
            except Exception as e:
                failed += 1
                failed_files.append(blob_name)
                logger.error(f"  ✗ Failed: {blob_name} - {str(e)}")
                continue
        
        logger.info("=" * 60)
        logger.info(f"Copy completed: {copied} succeeded, {failed} failed")
        logger.info("=" * 60)
        
        if failed_files:
            logger.warning(f"Failed files: {failed_files}")
        
        return {
            'status': 'completed',
            'total_files': len(matching_blobs),
            'files_copied': copied,
            'files_failed': failed,
            'failed_files': failed_files if failed > 0 else []
        }
        
    except Exception as e:
        logger.error(f"✗ Copy operation failed: {str(e)}")
        raise


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
    description='Generic DAG to copy files between Azure Blob Storage containers',
    schedule=None,  # Manual trigger only
    catchup=False,
    tags=['azure', 'blob', 'copy', 'generic', 'reusable'],
    params={
        # Default example - change when triggering
        'source_container': 'sg-analytics-raw',
        'target_container': 'airflow',
        'prefix': 'seasonal_buy/2025-10-13/',
        'file_pattern': '*',
        
        # Alternative single file example (commented):
        # 'source_container': 'raw-data',
        # 'target_container': 'processed-data',
        # 'source_path': 'sales/data.csv',
        # 'target_path': 'archive/sales/data.csv',
    }
) as dag:
    
    copy_task = PythonOperator(
        task_id='copy_files',
        python_callable=copy_azure_blobs,
        doc_md="""
        ## Copy Files Task
        
        This task copies files from source to target Azure Blob Storage container.
        
        ### Configuration Options:
        
        **Option 1: Copy Single File**
        ```json
        {
            "source_container": "raw-data",
            "target_container": "processed-data",
            "source_path": "sales/report.csv",
            "target_path": "archive/sales/report.csv"
        }
        ```
        
        **Option 2: Copy All Files in Folder**
        ```json
        {
            "source_container": "staging",
            "target_container": "production",
            "prefix": "daily-reports/2024-12/"
        }
        ```
        
        **Option 3: Copy Files by Pattern**
        ```json
        {
            "source_container": "raw-data",
            "target_container": "backup",
            "prefix": "logs/",
            "file_pattern": "*.log"
        }
        ```
        
        **Option 4: Copy CSV Files Only**
        ```json
        {
            "source_container": "sales",
            "target_container": "analytics",
            "prefix": "exports/",
            "file_pattern": "*.csv"
        }
        ```
        """
    )
