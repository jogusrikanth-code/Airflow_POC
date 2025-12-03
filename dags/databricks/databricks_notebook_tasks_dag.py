"""Databricks Notebook Task DAG
================================
Demonstrates calling Databricks notebooks as tasks with dependencies.

Examples:
- Run a notebook as a task
- Chain multiple notebook tasks
- Pass parameters to notebooks
"""

from airflow import DAG
from airflow.providers.databricks.operators.databricks import DatabricksSubmitRunOperator
from datetime import datetime, timedelta


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
    simple_notebook = DatabricksSubmitRunOperator(
        task_id='run_notebook_task',
        databricks_conn_id='databricks_default',
        notebook_task={
            'notebook_path': '/Workspace/Users/example@company.com/ETL_Notebook',
            'base_parameters': {
                'env': 'production',
                'date': '{{ ds }}'
            }
        },
        existing_cluster_id='{{ conn.databricks_default.extra_dejson.cluster_id }}'
    )
    
    # ETL Pipeline with dependencies: Extract >> Transform >> Load
    extract = DatabricksSubmitRunOperator(
        task_id='extract_data',
        databricks_conn_id='databricks_default',
        notebook_task={
            'notebook_path': '/Workspace/Shared/01_Extract_Data',
            'base_parameters': {
                'source': 'sql_server',
                'table': 'sales_data'
            }
        },
        existing_cluster_id='{{ conn.databricks_default.extra_dejson.cluster_id }}'
    )
    
    transform = DatabricksSubmitRunOperator(
        task_id='transform_data',
        databricks_conn_id='databricks_default',
        notebook_task={
            'notebook_path': '/Workspace/Shared/02_Transform_Data',
            'base_parameters': {
                'input_table': 'raw_sales',
                'output_table': 'transformed_sales'
            }
        },
        existing_cluster_id='{{ conn.databricks_default.extra_dejson.cluster_id }}'
    )
    
    load = DatabricksSubmitRunOperator(
        task_id='load_data',
        databricks_conn_id='databricks_default',
        notebook_task={
            'notebook_path': '/Workspace/Shared/03_Load_Data',
            'base_parameters': {
                'source_table': 'transformed_sales',
                'target_warehouse': 'analytics_dw'
            }
        },
        existing_cluster_id='{{ conn.databricks_default.extra_dejson.cluster_id }}'
    )
    
    # Define task dependencies
    simple_notebook
    extract >> transform >> load
