"""
Production-Ready Databricks ETL Pipeline
=========================================
Uses Airflow's native DatabricksSubmitRunOperator for:
- Automatic retry logic
- Better error handling
- Cleaner Airflow UI integration
- Xcom support for data passing

Connection: databricks_default
"""
from airflow import DAG
from airflow.providers.databricks.operators.databricks import DatabricksSubmitRunOperator
from datetime import datetime, timedelta

default_args = {
    'owner': 'airflow',
    'retries': 2,
    'retry_delay': timedelta(minutes=5),
    'timeout': 3600,  # 1 hour timeout
}

# Define notebook task
notebook_task = {
    "notebook_path": "/Users/placeholder@company.com/etl_notebook",
    "base_parameters": {
        "execution_date": "{{ ds }}",
        "environment": "production"
    }
}

# Define cluster configuration (Azure Databricks node types)
cluster_config = {
    "spark_version": "14.3.x-scala2.12",
    "node_type_id": "Standard_DS3_v2",  # Azure node type
    "num_workers": 2,
    "azure_attributes": {
        "availability": "ON_DEMAND",
        "zone_id": "eastus"
    },
    "timeout_minutes": 60
}

with DAG(
    'databricks_production_etl',
    default_args=default_args,
    description='Production ETL pipeline using native Databricks operator',
    schedule='0 2 * * *',  # Run daily at 2 AM
    start_date=datetime(2025, 1, 1),
    catchup=False,
    tags=['databricks', 'production', 'etl', 'native-operator'],
) as dag:
    
    # Extract task - Run extraction notebook
    extract_data = DatabricksSubmitRunOperator(
        task_id='extract_data',
        databricks_conn_id='databricks_default',
        new_cluster=cluster_config,
        notebook_task={
            "notebook_path": "/Users/placeholder@company.com/extract",
            "base_parameters": {
                "date": "{{ ds }}",
                "mode": "full"
            }
        },
        polling_period_seconds=10,
        timeout_seconds=3600,
    )
    
    # Transform task - Run transformation notebook
    transform_data = DatabricksSubmitRunOperator(
        task_id='transform_data',
        databricks_conn_id='databricks_default',
        new_cluster=cluster_config,
        notebook_task={
            "notebook_path": "/Users/placeholder@company.com/transform",
            "base_parameters": {
                "date": "{{ ds }}",
                "quality_check": "enabled"
            }
        },
        polling_period_seconds=10,
        timeout_seconds=3600,
    )
    
    # Load task - Run load notebook
    load_data = DatabricksSubmitRunOperator(
        task_id='load_data',
        databricks_conn_id='databricks_default',
        new_cluster=cluster_config,
        notebook_task={
            "notebook_path": "/Users/placeholder@company.com/load",
            "base_parameters": {
                "date": "{{ ds }}",
                "target": "production_warehouse"
            }
        },
        polling_period_seconds=10,
        timeout_seconds=3600,
    )
    
    # Validation task
    validate_data = DatabricksSubmitRunOperator(
        task_id='validate_data',
        databricks_conn_id='databricks_default',
        new_cluster=cluster_config,
        notebook_task={
            "notebook_path": "/Users/placeholder@company.com/validate",
            "base_parameters": {
                "date": "{{ ds }}",
                "strict_mode": "true"
            }
        },
        polling_period_seconds=10,
        timeout_seconds=1800,
    )
    
    # Define task dependencies
    extract_data >> transform_data >> load_data >> validate_data
