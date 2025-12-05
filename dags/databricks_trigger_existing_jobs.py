"""
Trigger Databricks Jobs
========================
Triggers existing Databricks jobs in sequence.

What you need:
1. Jobs already created in Databricks
2. Job IDs (use 'list_databricks_jobs' DAG to find them)
3. Connection 'databricks_default' configured

How to use:
1. Find your job IDs (run 'list_databricks_jobs' DAG)
2. Update JOB_IDS below (line 19-21)
3. Enable the DAG and run
"""
from airflow import DAG
from airflow.providers.databricks.operators.databricks import DatabricksRunNowOperator
from datetime import datetime

# Configuration - UPDATE THESE WITH YOUR JOB IDS
JOB_IDS = {
    "ingest": 123,   # Replace with your ingestion job ID
    "process": 124,  # Replace with your processing job ID
    "quality": 125   # Replace with your quality check job ID
}

with DAG(
    dag_id='databricks_trigger_existing_jobs',
    description='Trigger 3 Databricks jobs: Ingest → Process → Quality',
    schedule='0 6 * * *',  # Runs daily at 6 AM UTC
    start_date=datetime(2025, 1, 1),
    catchup=False,
    tags=['databricks', 'jobs', 'simple'],
) as dag:
    
    # Job 1: Data Ingestion
    ingest = DatabricksRunNowOperator(
        task_id='ingest_data',
        databricks_conn_id='databricks_default',
        job_id=JOB_IDS["ingest"],
    )
    
    # Job 2: Data Processing
    process = DatabricksRunNowOperator(
        task_id='process_data',
        databricks_conn_id='databricks_default',
        job_id=JOB_IDS["process"],
    )
    
    # Job 3: Quality Check
    quality = DatabricksRunNowOperator(
        task_id='quality_check',
        databricks_conn_id='databricks_default',
        job_id=JOB_IDS["quality"],
    )
    
    # Define the flow
    ingest >> process >> quality
