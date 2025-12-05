"""
Databricks Data Quality & Monitoring
=====================================
Implement data quality checks and monitoring.

What this demonstrates:
- Running data quality checks
- Validating schema
- Checking data completeness
- Monitoring data freshness
- Alerting on quality issues

Connection: databricks_default
"""
from airflow import DAG
from airflow.providers.databricks.operators.databricks import DatabricksSubmitRunOperator
from airflow.operators.python import PythonOperator, BranchPythonOperator
from datetime import datetime

CLUSTER = {
    "spark_version": "14.3.x-scala2.12",
    "node_type_id": "Standard_DS3_v2",
    "num_workers": 2
}

with DAG(
    dag_id='databricks_data_quality',
    description='Data quality checks and monitoring',
    schedule='0 */4 * * *',  # Every 4 hours
    start_date=datetime(2025, 1, 1),
    catchup=False,
    tags=['databricks', 'data-quality', 'monitoring', 'sample'],
) as dag:
    
    # Task 1: Schema validation
    validate_schema = DatabricksSubmitRunOperator(
        task_id='validate_schema',
        databricks_conn_id='databricks_default',
        new_cluster=CLUSTER,
        notebook_task={
            "notebook_path": "/Workspace/quality/validate_schema",
            "base_parameters": {
                "table": "sales_data",
                "expected_schema": "order_id:int,amount:decimal,date:date"
            }
        },
    )
    
    # Task 2: Check completeness
    check_completeness = DatabricksSubmitRunOperator(
        task_id='check_completeness',
        databricks_conn_id='databricks_default',
        new_cluster=CLUSTER,
        spark_python_task={
            "python_file": "dbfs:/quality/check_nulls.py",
            "parameters": ["--table", "sales_data", "--threshold", "0.05"]
        },
    )
    
    # Task 3: Check uniqueness
    check_uniqueness = DatabricksSubmitRunOperator(
        task_id='check_uniqueness',
        databricks_conn_id='databricks_default',
        new_cluster=CLUSTER,
        spark_sql_task={
            "query": {
                "query": """
                SELECT 
                    COUNT(*) as total_rows,
                    COUNT(DISTINCT order_id) as unique_orders,
                    COUNT(*) - COUNT(DISTINCT order_id) as duplicates
                FROM sales_data
                """
            }
        },
    )
    
    # Task 4: Check data freshness
    check_freshness = DatabricksSubmitRunOperator(
        task_id='check_data_freshness',
        databricks_conn_id='databricks_default',
        new_cluster=CLUSTER,
        spark_sql_task={
            "query": {
                "query": """
                SELECT 
                    MAX(created_at) as latest_record,
                    DATEDIFF(NOW(), MAX(created_at)) as days_old
                FROM sales_data
                """
            }
        },
    )
    
    # Task 5: Check data ranges
    check_ranges = DatabricksSubmitRunOperator(
        task_id='check_data_ranges',
        databricks_conn_id='databricks_default',
        new_cluster=CLUSTER,
        spark_sql_task={
            "query": {
                "query": """
                SELECT 
                    MIN(amount) as min_amount,
                    MAX(amount) as max_amount,
                    AVG(amount) as avg_amount,
                    COUNT(*) FILTER (WHERE amount < 0) as negative_values
                FROM sales_data
                """
            }
        },
    )
    
    def evaluate_quality(**context):
        """Evaluate all quality checks and decide next steps"""
        # Get results from previous tasks
        schema_result = context['ti'].xcom_pull(task_ids='validate_schema')
        completeness = context['ti'].xcom_pull(task_ids='check_completeness')
        
        # Simple decision logic
        if schema_result == 'passed' and completeness > 0.95:
            return 'send_success_notification'
        else:
            return 'send_failure_alert'
    
    # Branching based on quality
    evaluate = BranchPythonOperator(
        task_id='evaluate_quality',
        python_callable=evaluate_quality,
    )
    
    def send_success():
        print("✅ All quality checks passed!")
    
    def send_alert():
        print("⚠️ Quality checks failed - alerting team")
    
    success = PythonOperator(task_id='send_success_notification', python_callable=send_success)
    failure = PythonOperator(task_id='send_failure_alert', python_callable=send_alert)
    
    # Flow
    [validate_schema, check_completeness, check_uniqueness, check_freshness, check_ranges] >> evaluate
    evaluate >> [success, failure]
