"""Azure Blob List Operations DAG
================================
Demonstrates listing blobs and containers in Azure Storage.

Examples:
- List all blobs in a container
- List blobs with specific prefix
"""

from airflow import DAG
from airflow.operators.python import PythonOperator
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)


def list_all_blobs(**context):
    """List all blobs in a container."""
    from src.connectors import get_azure_storage_connector
    
    azure = get_azure_storage_connector('azure_default')
    
    container = 'staging'
    
    logger.info(f"Listing all blobs in container: {container}")
    
    # List all blobs
    blobs = azure.list_blobs(container)
    
    logger.info(f"✓ Found {len(blobs)} blobs")
    
    # Log first 10 for visibility
    for blob in blobs[:10]:
        logger.info(f"  - {blob}")
    
    if len(blobs) > 10:
        logger.info(f"  ... and {len(blobs) - 10} more")
    
    return {'container': container, 'blob_count': len(blobs), 'blobs': blobs}


def list_blobs_by_prefix(**context):
    """List blobs matching a specific prefix (folder path)."""
    from src.connectors import get_azure_storage_connector
    
    azure = get_azure_storage_connector('azure_default')
    
    container = 'staging'
    prefix = 'sales/'
    
    logger.info(f"Listing blobs in {container} with prefix: {prefix}")
    
    # List blobs with prefix
    blobs = azure.list_blobs(container, prefix=prefix)
    
    logger.info(f"✓ Found {len(blobs)} blobs matching prefix '{prefix}'")
    
    for blob in blobs:
        logger.info(f"  - {blob}")
    
    return {'container': container, 'prefix': prefix, 'blob_count': len(blobs), 'blobs': blobs}


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
    'azure_blob_list_operations',
    default_args=default_args,
    description='List blobs and containers in Azure Storage',
    schedule='@daily',
    catchup=False,
    tags=['azure', 'blob', 'list', 'example'],
) as dag:
    
    # Task 1: List all blobs in container
    list_all = PythonOperator(
        task_id='list_all_blobs',
        python_callable=list_all_blobs,
    )
    
    # Task 2: List blobs by prefix
    list_prefix = PythonOperator(
        task_id='list_blobs_by_prefix',
        python_callable=list_blobs_by_prefix,
    )
    
    # Tasks run independently
    [list_all, list_prefix]
