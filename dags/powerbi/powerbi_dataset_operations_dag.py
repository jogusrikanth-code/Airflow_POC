"""Power BI Dataset Operations DAG
===================================
Demonstrates listing and managing Power BI datasets.

Examples:
- List all datasets in a workspace
- Refresh a specific dataset
"""

from airflow import DAG
from airflow.operators.python import PythonOperator
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)


def list_datasets(**context):
    """List all datasets in a Power BI workspace."""
    from src.connectors import get_powerbi_connector
    
    pbi = get_powerbi_connector('powerbi_default')
    
    # Replace with your workspace ID
    workspace_id = 'your-workspace-id'
    
    logger.info(f"Listing datasets in workspace: {workspace_id}")
    
    datasets = pbi.list_datasets(workspace_id)
    
    logger.info(f"✓ Found {len(datasets)} datasets")
    
    for dataset in datasets:
        dataset_id = dataset.get('id')
        dataset_name = dataset.get('name')
        logger.info(f"  - {dataset_name} ({dataset_id})")
    
    return {'workspace_id': workspace_id, 'dataset_count': len(datasets), 'datasets': datasets}


def refresh_dataset(**context):
    """Refresh a Power BI dataset."""
    from src.connectors import get_powerbi_connector
    
    pbi = get_powerbi_connector('powerbi_default')
    
    # Replace with your workspace and dataset IDs
    workspace_id = 'your-workspace-id'
    dataset_id = 'your-dataset-id'
    
    logger.info(f"Refreshing dataset: {dataset_id}")
    
    success = pbi.refresh_dataset(
        workspace_id=workspace_id,
        dataset_id=dataset_id,
        wait_for_completion=True,
        timeout=300
    )
    
    if success:
        logger.info("✓ Dataset refresh completed successfully")
    else:
        logger.error("✗ Dataset refresh failed")
        raise Exception("Dataset refresh failed")
    
    return {'workspace_id': workspace_id, 'dataset_id': dataset_id, 'status': 'success'}


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
    'powerbi_dataset_operations',
    default_args=default_args,
    description='List and refresh Power BI datasets',
    schedule='@daily',
    catchup=False,
    tags=['powerbi', 'dataset', 'refresh', 'example'],
) as dag:
    
    # Task 1: List all datasets
    list_all_datasets = PythonOperator(
        task_id='list_datasets',
        python_callable=list_datasets,
    )
    
    # Task 2: Refresh dataset
    refresh = PythonOperator(
        task_id='refresh_dataset',
        python_callable=refresh_dataset,
    )
    
    # Tasks run independently
    [list_all_datasets, refresh]
