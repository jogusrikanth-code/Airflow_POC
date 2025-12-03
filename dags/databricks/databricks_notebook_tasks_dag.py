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
