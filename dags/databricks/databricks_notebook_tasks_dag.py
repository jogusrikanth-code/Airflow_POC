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


def run_notebook_task(**context):
    """Run a Databricks notebook as a one-time task."""
    from src.connectors import get_databricks_connector
    
    db = get_databricks_connector('databricks_default')
    
    # Notebook configuration
    notebook_path = "/Workspace/Users/example@company.com/ETL_Notebook"
    cluster_id = db.cluster_id
    
    logger.info(f"Running notebook: {notebook_path}")
    
    url = f"https://{db.host}/api/2.1/jobs/runs/submit"
    payload = {
        'run_name': 'Airflow triggered notebook run',
        'existing_cluster_id': cluster_id,
        'notebook_task': {
            'notebook_path': notebook_path,
            'base_parameters': {
                'env': 'production',
                'date': '{{ ds }}'
            }
        }
    }
    
    response = db.session.post(url, json=payload)
    response.raise_for_status()
    
    run_id = response.json().get('run_id')
    
    logger.info(f"✓ Notebook started with run_id: {run_id}")
    
    return {'notebook': notebook_path, 'run_id': run_id}


def run_data_extraction_notebook(**context):
    """First task: Extract data from source."""
    from src.connectors import get_databricks_connector
    
    db = get_databricks_connector('databricks_default')
    
    notebook_path = "/Workspace/Shared/01_Extract_Data"
    
    logger.info(f"Step 1: Running extraction notebook: {notebook_path}")
    
    url = f"https://{db.host}/api/2.1/jobs/runs/submit"
    payload = {
        'run_name': 'Extract Data',
        'existing_cluster_id': db.cluster_id,
        'notebook_task': {
            'notebook_path': notebook_path,
            'base_parameters': {
                'source': 'sql_server',
                'table': 'sales_data'
            }
        }
    }
    
    response = db.session.post(url, json=payload)
    response.raise_for_status()
    
    run_id = response.json().get('run_id')
    logger.info(f"✓ Extraction started: {run_id}")
    
    return {'step': 'extract', 'run_id': run_id}


def run_data_transformation_notebook(**context):
    """Second task: Transform extracted data."""
    from src.connectors import get_databricks_connector
    
    db = get_databricks_connector('databricks_default')
    
    notebook_path = "/Workspace/Shared/02_Transform_Data"
    
    logger.info(f"Step 2: Running transformation notebook: {notebook_path}")
    
    url = f"https://{db.host}/api/2.1/jobs/runs/submit"
    payload = {
        'run_name': 'Transform Data',
        'existing_cluster_id': db.cluster_id,
        'notebook_task': {
            'notebook_path': notebook_path,
            'base_parameters': {
                'input_table': 'raw_sales',
                'output_table': 'transformed_sales'
            }
        }
    }
    
    response = db.session.post(url, json=payload)
    response.raise_for_status()
    
    run_id = response.json().get('run_id')
    logger.info(f"✓ Transformation started: {run_id}")
    
    return {'step': 'transform', 'run_id': run_id}


def run_data_load_notebook(**context):
    """Third task: Load transformed data to target."""
    from src.connectors import get_databricks_connector
    
    db = get_databricks_connector('databricks_default')
    
    notebook_path = "/Workspace/Shared/03_Load_Data"
    
    logger.info(f"Step 3: Running load notebook: {notebook_path}")
    
    url = f"https://{db.host}/api/2.1/jobs/runs/submit"
    payload = {
        'run_name': 'Load Data',
        'existing_cluster_id': db.cluster_id,
        'notebook_task': {
            'notebook_path': notebook_path,
            'base_parameters': {
                'source_table': 'transformed_sales',
                'target_warehouse': 'analytics_dw'
            }
        }
    }
    
    response = db.session.post(url, json=payload)
    response.raise_for_status()
    
    run_id = response.json().get('run_id')
    logger.info(f"✓ Load started: {run_id}")
    
    return {'step': 'load', 'run_id': run_id}


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
        python_callable=run_notebook_task,
    )
    
    # ETL Pipeline with dependencies: Extract >> Transform >> Load
    extract = PythonOperator(
        task_id='extract_data',
        python_callable=run_data_extraction_notebook,
    )
    
    transform = PythonOperator(
        task_id='transform_data',
        python_callable=run_data_transformation_notebook,
    )
    
    load = PythonOperator(
        task_id='load_data',
        python_callable=run_data_load_notebook,
    )
    
    # Define task dependencies
    simple_notebook
    extract >> transform >> load
