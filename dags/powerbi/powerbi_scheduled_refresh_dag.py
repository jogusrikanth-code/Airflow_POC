"""Power BI Scheduled Refresh DAG
==================================
Demonstrates scheduled dataset refreshes with dependencies.

Examples:
- Refresh multiple datasets in sequence
- Chain refreshes with dependencies
"""

from airflow import DAG
from airflow.operators.python import PythonOperator
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)


def refresh_source_dataset(**context):
    """Refresh the source dataset first."""
    from src.connectors import get_powerbi_connector
    
    pbi = get_powerbi_connector('powerbi_default')
    
    workspace_id = 'your-workspace-id'
    dataset_id = 'source-dataset-id'
    
    logger.info(f"Step 1: Refreshing source dataset: {dataset_id}")
    
    success = pbi.refresh_dataset(
        workspace_id=workspace_id,
        dataset_id=dataset_id,
        wait_for_completion=True,
        timeout=600
    )
    
    if success:
        logger.info("✓ Source dataset refreshed")
    else:
        raise Exception("Source dataset refresh failed")
    
    return {'dataset_id': dataset_id, 'status': 'success'}


def refresh_dependent_dataset(**context):
    """Refresh a dataset that depends on the source dataset."""
    from src.connectors import get_powerbi_connector
    
    pbi = get_powerbi_connector('powerbi_default')
    
    workspace_id = 'your-workspace-id'
    dataset_id = 'dependent-dataset-id'
    
    logger.info(f"Step 2: Refreshing dependent dataset: {dataset_id}")
    
    success = pbi.refresh_dataset(
        workspace_id=workspace_id,
        dataset_id=dataset_id,
        wait_for_completion=True,
        timeout=600
    )
    
    if success:
        logger.info("✓ Dependent dataset refreshed")
    else:
        raise Exception("Dependent dataset refresh failed")
    
    return {'dataset_id': dataset_id, 'status': 'success'}


def refresh_dashboard_dataset(**context):
    """Refresh the final dashboard dataset."""
    from src.connectors import get_powerbi_connector
    
    pbi = get_powerbi_connector('powerbi_default')
    
    workspace_id = 'your-workspace-id'
    dataset_id = 'dashboard-dataset-id'
    
    logger.info(f"Step 3: Refreshing dashboard dataset: {dataset_id}")
    
    success = pbi.refresh_dataset(
        workspace_id=workspace_id,
        dataset_id=dataset_id,
        wait_for_completion=True,
        timeout=600
    )
    
    if success:
        logger.info("✓ Dashboard dataset refreshed")
    else:
        raise Exception("Dashboard dataset refresh failed")
    
    return {'dataset_id': dataset_id, 'status': 'success'}


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
    'powerbi_scheduled_refresh',
    default_args=default_args,
    description='Scheduled Power BI dataset refreshes with dependencies',
    schedule='0 6 * * *',  # Run daily at 6 AM
    catchup=False,
    tags=['powerbi', 'refresh', 'scheduled', 'example'],
) as dag:
    
    # Refresh chain: Source >> Dependent >> Dashboard
    refresh_source = PythonOperator(
        task_id='refresh_source_dataset',
        python_callable=refresh_source_dataset,
    )
    
    refresh_dependent = PythonOperator(
        task_id='refresh_dependent_dataset',
        python_callable=refresh_dependent_dataset,
    )
    
    refresh_dashboard = PythonOperator(
        task_id='refresh_dashboard_dataset',
        python_callable=refresh_dashboard_dataset,
    )
    
    # Define dependencies: ensure source refreshes before dependent
    refresh_source >> refresh_dependent >> refresh_dashboard
