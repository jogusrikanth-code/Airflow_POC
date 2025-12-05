"""
Databricks Native Operator Example
===================================
Uses Airflow's built-in DatabricksSubmitRunOperator
instead of PythonOperator + SDK.

This is the Airflow-native way to interact with Databricks.
"""
from airflow import DAG
from airflow.providers.databricks.operators.databricks import DatabricksSubmitRunOperator
from datetime import datetime, timedelta

default_args = {
    'owner': 'airflow',
    'retries': 1,
    'retry_delay': timedelta(minutes=1),
}

# Task definition for Databricks
notebook_task = {
    "notebook_path": "/Users/your-email@company.com/test_notebook",
    "base_parameters": {
        "env": "dev",
        "date": "{{ ds }}"
    }
}

with DAG(
    'databricks_native_operator_example',
    default_args=default_args,
    description='Example using Airflow native Databricks DatabricksSubmitRunOperator',
    schedule=None,
    start_date=datetime(2025, 1, 1),
    catchup=False,
    tags=['databricks', 'native-operator', 'example'],
) as dag:
    
    # This is the Airflow-native way to run Databricks jobs
    submit_notebook = DatabricksSubmitRunOperator(
        task_id='run_databricks_notebook',
        databricks_conn_id='databricks_default',
        new_cluster={
            "spark_version": "14.3.x-scala2.12",
            "node_type_id": "i3.xlarge",
            "num_workers": 2,
            "aws_attributes": {
                "availability": "SPOT"
            }
        },
        notebook_task=notebook_task,
        # Optional: polling and retry configuration
        polling_period_seconds=5,
        timeout_seconds=3600,
    )

# Another example: Run an existing job
from airflow.providers.databricks.operators.databricks import DatabricksRunNowOperator

with DAG(
    'databricks_run_job_operator_example',
    default_args=default_args,
    description='Example using Airflow native DatabricksRunNowOperator to run existing job',
    schedule=None,
    start_date=datetime(2025, 1, 1),
    catchup=False,
    tags=['databricks', 'native-operator', 'job-run'],
) as dag:
    
    # Run an existing Databricks job
    run_job = DatabricksRunNowOperator(
        task_id='run_existing_databricks_job',
        databricks_conn_id='databricks_default',
        job_id=123,  # Replace with your job ID
        notebook_params={
            "key": "value",
            "param2": "value2"
        }
    )
