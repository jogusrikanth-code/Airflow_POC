"""Databricks Notebook Task DAG
================================
Demonstrates calling Databricks notebooks as tasks with dependencies.

Examples:
- Run a notebook as a task
- Chain multiple notebook tasks
- Pass parameters to notebooks
"""

from airflow import DAG
from airflow.operators.python import PythonOperator
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)


def run_notebook(**context):
    """Run a Databricks notebook."""
    from src.connectors import get_databricks_connector
    
    db = get_databricks_connector('databricks_default')
    notebook_path = context.get('params', {}).get('notebook_path')
    
    logger.info(f"Running notebook: {notebook_path}")
    
    url = f"https://{db.host}/api/2.1/jobs/runs/submit"
    payload = {
        'run_name': f"Airflow: {context['task_instance'].task_id}",
        'existing_cluster_id': db.cluster_id,
        'notebook_task': {
            'notebook_path': notebook_path,
            'base_parameters': context.get('params', {}).get('parameters', {})
        }
    }
    
    response = db.session.post(url, json=payload)
    response.raise_for_status()
    
    run_id = response.json().get('run_id')
    logger.info(f"✓ Notebook started: {run_id}")
    
    return {'notebook': notebook_path, 'run_id': run_id}


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
    'databricks_notebook_tasks',
    default_args=default_args,
    description='Run Databricks notebooks as tasks with dependencies',
    schedule='@daily',
    catchup=False,
    tags=['databricks', 'notebook', 'etl', 'example'],
) as dag:
    
    # Simple single notebook task
    simple_notebook = PythonOperator(
        task_id='run_notebook_task',
        python_callable=run_notebook,
        params={
            'notebook_path': '/Workspace/Users/example@company.com/ETL_Notebook',
            'parameters': {'env': 'production'}
        }
    )
    
    # ETL Pipeline with dependencies: Extract >> Transform >> Load
    extract = PythonOperator(
        task_id='extract_data',
        python_callable=run_notebook,
        params={
            'notebook_path': '/Workspace/Shared/01_Extract_Data',
            'parameters': {'source': 'sql_server', 'table': 'sales_data'}
        }
    )
    
    transform = PythonOperator(
        task_id='transform_data',
        python_callable=run_notebook,
        params={
            'notebook_path': '/Workspace/Shared/02_Transform_Data',
            'parameters': {'input_table': 'raw_sales', 'output_table': 'transformed_sales'}
        }
    )
    
    load = PythonOperator(
        task_id='load_data',
        python_callable=run_notebook,
        params={
            'notebook_path': '/Workspace/Shared/03_Load_Data',
            'parameters': {'source_table': 'transformed_sales', 'target_warehouse': 'analytics_dw'}
        }
    )
    
    # Define task dependencies
    simple_notebook
    extract >> transform >> load
