"""Databricks Workflow Operations DAG
=====================================
Demonstrates listing and executing Databricks workflows (Jobs).

Examples:
- List all workflows
- Execute a workflow
"""

from airflow import DAG
from airflow.operators.python import PythonOperator
from datetime import datetime, timedelta
import logging
import time

logger = logging.getLogger(__name__)


def list_workflows(**context):
    """List all workflows (jobs) in Databricks workspace."""
    from src.connectors import get_databricks_connector
    
    db = get_databricks_connector('databricks_default')
    
    logger.info("Listing all workflows...")
    
    url = f"https://{db.host}/api/2.1/jobs/list"
    response = db.session.get(url)
    response.raise_for_status()
    
    jobs = response.json().get('jobs', [])
    
    logger.info(f"✓ Found {len(jobs)} workflows")
    
    for job in jobs[:10]:  # Show first 10
        job_id = job.get('job_id')
        job_name = job.get('settings', {}).get('name', 'Unnamed')
        logger.info(f"  - {job_name} (ID: {job_id})")
    
    return {'workflow_count': len(jobs), 'workflows': jobs}


def execute_workflow(**context):
    """Execute a Databricks workflow by job ID."""
    from src.connectors import get_databricks_connector
    
    db = get_databricks_connector('databricks_default')
    
    # Example job_id - replace with actual job ID
    job_id = 123456
    
    logger.info(f"Executing workflow: {job_id}")
    
    url = f"https://{db.host}/api/2.1/jobs/run-now"
    payload = {'job_id': job_id}
    
    response = db.session.post(url, json=payload)
    response.raise_for_status()
    
    run_id = response.json().get('run_id')
    
    logger.info(f"✓ Workflow started with run_id: {run_id}")
    
    return {'job_id': job_id, 'run_id': run_id, 'status': 'started'}


def check_workflow_status(**context):
    """Check status of a workflow run."""
    from src.connectors import get_databricks_connector
    
    db = get_databricks_connector('databricks_default')
    
    # Get run_id from previous task
    ti = context['task_instance']
    result = ti.xcom_pull(task_ids='execute_workflow')
    
    if not result:
        logger.info("No workflow run to check")
        return {'status': 'skipped'}
    
    run_id = result.get('run_id')
    
    logger.info(f"Checking status for run_id: {run_id}")
    
    url = f"https://{db.host}/api/2.1/jobs/runs/get"
    response = db.session.get(url, params={'run_id': run_id})
    response.raise_for_status()
    
    run_details = response.json()
    state = run_details.get('state', {})
    life_cycle_state = state.get('life_cycle_state')
    result_state = state.get('result_state')
    
    logger.info(f"✓ Run status: {life_cycle_state}")
    if result_state:
        logger.info(f"  Result: {result_state}")
    
    return {
        'run_id': run_id,
        'life_cycle_state': life_cycle_state,
        'result_state': result_state
    }


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
    
    # Task 2: Execute workflow
    execute = PythonOperator(
        task_id='execute_workflow',
        python_callable=execute_workflow,
    )
    
    # Task 3: Check workflow status
    check_status = PythonOperator(
        task_id='check_workflow_status',
        python_callable=check_workflow_status,
    )
    
    # Define dependencies
    list_all_workflows
    execute >> check_status
