"""
List Databricks Jobs
====================
Shows all jobs in your Databricks workspace.

What you need:
- Connection 'databricks_default' configured in Airflow

What it does:
- Lists all job IDs and names
- Shows job details
- Use these IDs in other DAGs
"""
from airflow import DAG
from airflow.operators.python import PythonOperator
from datetime import datetime

with DAG(
    dag_id='databricks_utility_list_jobs',
    description='List all Databricks jobs with IDs',
    schedule=None,  # Run manually
    start_date=datetime(2025, 1, 1),
    catchup=False,
    tags=['databricks', 'utility'],
) as dag:
    
    def list_jobs():
        """Get and print all Databricks jobs"""
        from databricks.sdk import WorkspaceClient
        from airflow.hooks.base import BaseHook
        
        # Connect to Databricks
        conn = BaseHook.get_connection('databricks_default')
        client = WorkspaceClient(host=conn.host, token=conn.password)
        
        # Get all jobs
        jobs = list(client.jobs.list())
        
        # Print results
        print("\n" + "="*60)
        print(f"Found {len(jobs)} job(s) in Databricks workspace")
        print("="*60)
        
        if jobs:
            for job in jobs:
                print(f"\nJob ID: {job.job_id}")
                print(f"Name: {job.settings.name}")
                print(f"Created: {job.created_time}")
        else:
            print("\nNo jobs found. Create jobs in Databricks first.")
        
        return {'total_jobs': len(jobs)}
    
    # Single task
    list_task = PythonOperator(
        task_id='list_all_jobs',
        python_callable=list_jobs,
    )
