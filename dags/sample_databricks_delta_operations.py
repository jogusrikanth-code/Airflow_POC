"""
Databricks Delta Lake Operations
=================================
Work with Delta Lake tables: create, merge, update, time travel.

What this demonstrates:
- Creating Delta tables
- Merge operations (UPSERT)
- Update/Delete operations
- Time travel queries
- Table versioning

Connection: databricks_default
"""
from airflow import DAG
from airflow.providers.databricks.operators.databricks import DatabricksSubmitRunOperator
from datetime import datetime

# Cluster for all tasks
CLUSTER = {
    "spark_version": "14.3.x-scala2.12",
    "node_type_id": "Standard_DS3_v2",
    "num_workers": 2
}

with DAG(
    dag_id='databricks_delta_operations',
    description='Delta Lake: merge, update, time travel',
    schedule=None,
    start_date=datetime(2025, 1, 1),
    catchup=False,
    tags=['databricks', 'delta-lake', 'sample'],
) as dag:
    
    # Task 1: Create Delta table
    create_table = DatabricksSubmitRunOperator(
        task_id='create_delta_table',
        databricks_conn_id='databricks_default',
        new_cluster=CLUSTER,
        spark_python_task={
            "python_file": "dbfs:/tmp/create_delta_table.py",
            "parameters": ["--table", "customers"]
        },
    )
    
    # Task 2: Merge (UPSERT) operation
    merge_data = DatabricksSubmitRunOperator(
        task_id='merge_upsert_data',
        databricks_conn_id='databricks_default',
        new_cluster=CLUSTER,
        spark_python_task={
            "python_file": "dbfs:/tmp/merge_customers.py"
        },
    )
    
    # Task 3: Update records
    update_records = DatabricksSubmitRunOperator(
        task_id='update_records',
        databricks_conn_id='databricks_default',
        new_cluster=CLUSTER,
        spark_sql_task={
            "query": {
                "query": """
                UPDATE customers 
                SET status = 'premium' 
                WHERE total_purchases > 10000
                """
            }
        },
    )
    
    # Task 4: Delete old records
    delete_old = DatabricksSubmitRunOperator(
        task_id='delete_old_records',
        databricks_conn_id='databricks_default',
        new_cluster=CLUSTER,
        spark_sql_task={
            "query": {
                "query": """
                DELETE FROM customers 
                WHERE last_purchase_date < '2024-01-01'
                """
            }
        },
    )
    
    # Task 5: Time travel query
    time_travel = DatabricksSubmitRunOperator(
        task_id='time_travel_query',
        databricks_conn_id='databricks_default',
        new_cluster=CLUSTER,
        spark_sql_task={
            "query": {
                "query": """
                SELECT * FROM customers VERSION AS OF 5
                -- Query table as it was 5 versions ago
                """
            }
        },
    )
    
    # Flow
    create_table >> merge_data >> update_records >> delete_old >> time_travel
