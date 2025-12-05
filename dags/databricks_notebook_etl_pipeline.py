"""
Simple Databricks ETL Pipeline
===============================
Runs 4 notebooks: Extract → Transform → Load → Validate

What you need:
1. Databricks workspace with notebooks created
2. Connection 'databricks_default' configured in Airflow

How to use:
1. Update notebook paths below (lines 29-32)
2. Adjust cluster size if needed (line 18)
3. Enable the DAG and run
"""
from airflow import DAG
from airflow.providers.databricks.operators.databricks import DatabricksSubmitRunOperator
from datetime import datetime

# Configuration
CLUSTER = {
    "spark_version": "14.3.x-scala2.12",
    "node_type_id": "Standard_DS3_v2",  # Small Azure node type
    "num_workers": 2
}

# Update these paths to match your Databricks notebooks
NOTEBOOKS = {
    "extract": "/Users/your-email@company.com/extract",      # Step 1
    "transform": "/Users/your-email@company.com/transform",  # Step 2
    "load": "/Users/your-email@company.com/load",           # Step 3
    "validate": "/Users/your-email@company.com/validate"    # Step 4
}

with DAG(
    dag_id='databricks_notebook_etl_pipeline',
    description='ETL Pipeline: Extract → Transform → Load → Validate',
    schedule='0 2 * * *',  # Runs daily at 2 AM UTC
    start_date=datetime(2025, 1, 1),
    catchup=False,
    tags=['databricks', 'etl', 'simple'],
) as dag:
    
    # Task 1: Extract
    extract = DatabricksSubmitRunOperator(
        task_id='extract',
        databricks_conn_id='databricks_default',
        new_cluster=CLUSTER,
        notebook_task={
            "notebook_path": NOTEBOOKS["extract"],
            "base_parameters": {"date": "{{ ds }}"}  # Passes execution date
        },
    )
    
    # Task 2: Transform
    transform = DatabricksSubmitRunOperator(
        task_id='transform',
        databricks_conn_id='databricks_default',
        new_cluster=CLUSTER,
        notebook_task={
            "notebook_path": NOTEBOOKS["transform"],
            "base_parameters": {"date": "{{ ds }}"}
        },
    )
    
    # Task 3: Load
    load = DatabricksSubmitRunOperator(
        task_id='load',
        databricks_conn_id='databricks_default',
        new_cluster=CLUSTER,
        notebook_task={
            "notebook_path": NOTEBOOKS["load"],
            "base_parameters": {"date": "{{ ds }}"}
        },
    )
    
    # Task 4: Validate
    validate = DatabricksSubmitRunOperator(
        task_id='validate',
        databricks_conn_id='databricks_default',
        new_cluster=CLUSTER,
        notebook_task={
            "notebook_path": NOTEBOOKS["validate"],
            "base_parameters": {"date": "{{ ds }}"}
        },
    )
    
    # Define the flow
    extract >> transform >> load >> validate
