"""Databricks Workflow Operations DAG
=====================================
Demonstrates listing and executing Databricks workflows (Jobs).

Examples:
- List all workflows
- Execute a workflow
"""

from airflow import DAG
from airflow.providers.databricks.operators.databricks import DatabricksRunNowOperator
from airflow.operators.python import PythonOperator
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)


def list_workflows(**context):
    """List all workflows (jobs) in Databricks workspace."""
    from airflow.providers.databricks.hooks.databricks import DatabricksHook
    
    hook = DatabricksHook(databricks_conn_id='databricks_default')
    
    logger.info("Listing all workflows...")
    
    response = hook._do_api_call(('GET', 'api/2.1/jobs/list'))
    jobs = response.get('jobs', [])
    
    logger.info(f"✓ Found {len(jobs)} workflows")
    
    for job in jobs[:10]:  # Show first 10
        job_id = job.get('job_id')
        job_name = job.get('settings', {}).get('name', 'Unnamed')
        logger.info(f"  - {job_name} (ID: {job_id})")
    
    return {'workflow_count': len(jobs), 'workflows': jobs}


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
    'databricks_workflow_operations',
    default_args=default_args,
    description='List and execute Databricks workflows',
    schedule='@daily',
    catchup=False,
    tags=['databricks', 'workflow', 'jobs', 'example'],
) as dag:
    
    # Task 1: List all workflows
    list_all_workflows = PythonOperator(
        task_id='list_workflows',
        python_callable=list_workflows,
    )
    
    # Task 2: Execute workflow using built-in operator
    # Replace job_id with actual workflow ID
    execute = DatabricksRunNowOperator(
        task_id='execute_workflow',
        databricks_conn_id='databricks_default',
        job_id=123456,  # Replace with actual job ID
    )
    
    # Tasks run independently
    [list_all_workflows, execute]
