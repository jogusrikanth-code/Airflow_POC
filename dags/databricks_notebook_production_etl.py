"""
Simple Databricks ETL Pipeline
==============================
Runs 4 notebooks in sequence: Extract → Transform → Load → Validate

Connection: databricks_default
Schedule: Daily at 2 AM

Setup Required:
1. Create notebooks in Databricks at the paths specified below
2. Update notebook paths to match your workspace
"""
from airflow import DAG
from airflow.providers.databricks.operators.databricks import DatabricksSubmitRunOperator
from datetime import datetime

# Cluster configuration - Update node type if needed
CLUSTER = {
    "spark_version": "14.3.x-scala2.12",
    "node_type_id": "Standard_DS3_v2",  # Azure node type
    "num_workers": 2,
    "timeout_minutes": 60
}

# DAG Definition
with DAG(
    dag_id='databricks_notebook_production_etl',
    description='Simple ETL: Extract → Transform → Load → Validate',
    schedule='0 2 * * *',  # Daily at 2 AM UTC
    start_date=datetime(2025, 1, 1),
    catchup=False,
    tags=['databricks', 'etl'],
) as dag:
    
    # Task 1: Extract data
    extract = DatabricksSubmitRunOperator(
        task_id='extract_data',
        databricks_conn_id='databricks_default',
        new_cluster=CLUSTER,
        notebook_task={
            "notebook_path": "/Users/your-email@company.com/extract",  # UPDATE THIS
            "base_parameters": {"date": "{{ ds }}"}
        },
    )
    
    # Task 2: Transform data
    transform = DatabricksSubmitRunOperator(
        task_id='transform_data',
        databricks_conn_id='databricks_default',
        new_cluster=CLUSTER,
        notebook_task={
            "notebook_path": "/Users/your-email@company.com/transform",  # UPDATE THIS
            "base_parameters": {"date": "{{ ds }}"}
        },
    )
    
    # Task 3: Load data
    load = DatabricksSubmitRunOperator(
        task_id='load_data',
        databricks_conn_id='databricks_default',
        new_cluster=CLUSTER,
        notebook_task={
            "notebook_path": "/Users/your-email@company.com/load",  # UPDATE THIS
            "base_parameters": {"date": "{{ ds }}"}
        },
    )
    
    # Task 4: Validate results
    validate = DatabricksSubmitRunOperator(
        task_id='validate_data',
        databricks_conn_id='databricks_default',
        new_cluster=CLUSTER,
        notebook_task={
            "notebook_path": "/Users/your-email@company.com/validate",  # UPDATE THIS
            "base_parameters": {"date": "{{ ds }}"}
        },
    )
    
    # Pipeline flow
    extract >> transform >> load >> validate
