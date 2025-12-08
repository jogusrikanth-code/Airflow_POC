"""
Trigger Databricks Workflows
=============================
Triggers existing Databricks workflows/jobs in sequence.

What you need:
1. Workflows/Jobs already created in Databricks
2. Job IDs (use 'databricks_utility_list_jobs' DAG to find them)
3. Connection 'databricks_default' configured

How to use:
1. Create workflows in Databricks (or use 'databricks_list_all_jobs' to find existing ones)
2. Update JOB_IDS below with your actual job IDs
3. Enable the DAG and run

Note: DatabricksRunNowOperator triggers existing workflows by job_id.
      Current workspace has 0 jobs - create workflows in Databricks first.
"""
from airflow import DAG
from airflow.providers.databricks.operators.databricks import DatabricksRunNowOperator
from datetime import datetime

# Configuration - UPDATE THESE WITH YOUR ACTUAL JOB IDS
# To find your job IDs, run 'databricks_utility_list_jobs' DAG or check Databricks UI
JOB_IDS = {
    "ingest": 123456789,   # Replace with your ingestion workflow job_id
    "process": 987654321,  # Replace with your processing workflow job_id
    "quality": 456789123   # Replace with your quality check workflow job_id
}

with DAG(
    dag_id='databricks_trigger_existing_jobs',
    description='Trigger existing Databricks workflows: Ingest → Process → Quality',
    schedule=None,  # Manual trigger - set schedule as needed
    start_date=datetime(2025, 1, 1),
    catchup=False,
    tags=['databricks', 'workflows', 'trigger'],
) as dag:
    
    # Workflow 1: Data Ingestion
    # Triggers existing Databricks workflow by job_id
    trigger_ingest = DatabricksRunNowOperator(
        task_id='trigger_ingest_workflow',
        databricks_conn_id='databricks_default',
        job_id=JOB_IDS["ingest"],
        # Optional: Pass parameters to the workflow
        # notebook_params={"source": "raw", "target": "bronze"},
    )
    
    # Workflow 2: Data Processing
    trigger_process = DatabricksRunNowOperator(
        task_id='trigger_process_workflow',
        databricks_conn_id='databricks_default',
        job_id=JOB_IDS["process"],
        # Optional: Pass parameters
        # notebook_params={"layer": "silver"},
    )
    
    # Workflow 3: Quality Check
    trigger_quality = DatabricksRunNowOperator(
        task_id='trigger_quality_workflow',
        databricks_conn_id='databricks_default',
        job_id=JOB_IDS["quality"],
        # Optional: Pass parameters
        # notebook_params={"threshold": "0.95"},
    )
    
    # Define the execution flow
    trigger_ingest >> trigger_process >> trigger_quality
