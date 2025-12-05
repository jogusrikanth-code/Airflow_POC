"""
Databricks Job Orchestration Pipeline
======================================
Uses DatabricksRunNowOperator to trigger existing jobs.
Perfect for orchestrating pre-configured Databricks jobs.

Connection: databricks_default
"""
from airflow import DAG
from airflow.providers.databricks.operators.databricks import DatabricksRunNowOperator
from datetime import datetime, timedelta

default_args = {
    'owner': 'airflow',
    'retries': 2,
    'retry_delay': timedelta(minutes=5),
}

with DAG(
    'databricks_job_orchestration',
    default_args=default_args,
    description='Orchestrate existing Databricks jobs using native operators',
    schedule='0 6 * * *',  # Run daily at 6 AM
    start_date=datetime(2025, 1, 1),
    catchup=False,
    tags=['databricks', 'job-orchestration', 'production'],
) as dag:
    
    # Job 1: Data ingestion job
    run_ingest_job = DatabricksRunNowOperator(
        task_id='run_data_ingestion_job',
        databricks_conn_id='databricks_default',
        job_id=123,  # Replace with your Databricks job ID
        polling_period_seconds=10,
    )
    
    # Job 2: Data processing job
    run_process_job = DatabricksRunNowOperator(
        task_id='run_data_processing_job',
        databricks_conn_id='databricks_default',
        job_id=124,  # Replace with your Databricks job ID
        polling_period_seconds=10,
    )
    
    # Job 3: Data quality check
    run_quality_job = DatabricksRunNowOperator(
        task_id='run_quality_check_job',
        databricks_conn_id='databricks_default',
        job_id=125,  # Replace with your Databricks job ID
        polling_period_seconds=10,
    )
    
    # Define dependencies
    run_ingest_job >> run_process_job >> run_quality_job
