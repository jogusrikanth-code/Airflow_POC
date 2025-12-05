"""
Trigger Existing Databricks Jobs
=================================
Triggers 3 pre-configured jobs in Databricks.

Connection: databricks_default
Schedule: Daily at 6 AM

Setup Required:
1. Create jobs in Databricks
2. Update job_id values below with your actual job IDs
3. Use 'databricks_list_workflows' DAG to find job IDs
"""
from airflow import DAG
from airflow.providers.databricks.operators.databricks import DatabricksRunNowOperator
from datetime import datetime

# DAG Definition
with DAG(
    dag_id='databricks_job_orchestration_pipeline',
    description='Trigger 3 Databricks jobs in sequence',
    schedule='0 6 * * *',  # Daily at 6 AM UTC
    start_date=datetime(2025, 1, 1),
    catchup=False,
    tags=['databricks', 'jobs'],
) as dag:
    
    # Job 1: Ingest data
    job1 = DatabricksRunNowOperator(
        task_id='ingest_data',
        databricks_conn_id='databricks_default',
        job_id=123,  # UPDATE: Replace with your job ID
    )
    
    # Job 2: Process data
    job2 = DatabricksRunNowOperator(
        task_id='process_data',
        databricks_conn_id='databricks_default',
        job_id=124,  # UPDATE: Replace with your job ID
    )
    
    # Job 3: Quality checks
    job3 = DatabricksRunNowOperator(
        task_id='quality_check',
        databricks_conn_id='databricks_default',
        job_id=125,  # UPDATE: Replace with your job ID
    )
    
    # Flow: Ingest → Process → Quality Check
    job1 >> job2 >> job3
