"""
Databricks Complete Pipeline
=============================
End-to-end data pipeline showcasing multiple Databricks capabilities.

What this demonstrates:
- Creating clusters dynamically
- Running notebooks in parallel
- Spark jobs (Python, SQL, JAR)
- Data quality checks
- Model training
- Conditional execution
- Error handling

Connection: databricks_default
"""
from airflow import DAG
from airflow.providers.databricks.operators.databricks import DatabricksSubmitRunOperator
from airflow.operators.python import PythonOperator
from airflow.operators.empty import EmptyOperator
from datetime import datetime

# Shared cluster configuration
CLUSTER = {
    "spark_version": "14.3.x-scala2.12",
    "node_type_id": "Standard_DS3_v2",
    "num_workers": 3,
    "autotermination_minutes": 30
}

with DAG(
    dag_id='databricks_complete_pipeline',
    description='Complete pipeline: ingest → transform → quality → model → deploy',
    schedule='0 3 * * *',  # Daily at 3 AM
    start_date=datetime(2025, 1, 1),
    catchup=False,
    tags=['databricks', 'complete', 'production', 'sample'],
) as dag:
    
    start = EmptyOperator(task_id='start')
    
    # Phase 1: Data Ingestion (Parallel)
    ingest_sales = DatabricksSubmitRunOperator(
        task_id='ingest_sales_data',
        databricks_conn_id='databricks_default',
        new_cluster=CLUSTER,
        notebook_task={
            "notebook_path": "/Workspace/pipelines/ingest/sales",
            "base_parameters": {"date": "{{ ds }}"}
        },
    )
    
    ingest_customers = DatabricksSubmitRunOperator(
        task_id='ingest_customer_data',
        databricks_conn_id='databricks_default',
        new_cluster=CLUSTER,
        notebook_task={
            "notebook_path": "/Workspace/pipelines/ingest/customers",
            "base_parameters": {"date": "{{ ds }}"}
        },
    )
    
    ingest_products = DatabricksSubmitRunOperator(
        task_id='ingest_product_data',
        databricks_conn_id='databricks_default',
        new_cluster=CLUSTER,
        notebook_task={
            "notebook_path": "/Workspace/pipelines/ingest/products",
            "base_parameters": {"date": "{{ ds }}"}
        },
    )
    
    # Phase 2: Data Transformation
    transform = DatabricksSubmitRunOperator(
        task_id='transform_data',
        databricks_conn_id='databricks_default',
        new_cluster=CLUSTER,
        notebook_task={
            "notebook_path": "/Workspace/pipelines/transform/join_tables",
            "base_parameters": {
                "date": "{{ ds }}",
                "output": "gold.sales_enriched"
            }
        },
    )
    
    # Phase 3: Data Quality
    quality_checks = DatabricksSubmitRunOperator(
        task_id='run_quality_checks',
        databricks_conn_id='databricks_default',
        new_cluster=CLUSTER,
        spark_python_task={
            "python_file": "dbfs:/quality/comprehensive_checks.py",
            "parameters": ["--table", "gold.sales_enriched"]
        },
    )
    
    # Phase 4: Aggregations (Parallel)
    daily_summary = DatabricksSubmitRunOperator(
        task_id='create_daily_summary',
        databricks_conn_id='databricks_default',
        new_cluster=CLUSTER,
        spark_sql_task={
            "query": {
                "query": """
                CREATE OR REPLACE TABLE gold.daily_sales_summary AS
                SELECT 
                    DATE(order_date) as date,
                    product_category,
                    COUNT(*) as order_count,
                    SUM(amount) as total_revenue
                FROM gold.sales_enriched
                WHERE order_date = '{{ ds }}'
                GROUP BY DATE(order_date), product_category
                """
            }
        },
    )
    
    customer_summary = DatabricksSubmitRunOperator(
        task_id='create_customer_summary',
        databricks_conn_id='databricks_default',
        new_cluster=CLUSTER,
        spark_sql_task={
            "query": {
                "query": """
                CREATE OR REPLACE TABLE gold.customer_metrics AS
                SELECT 
                    customer_id,
                    COUNT(*) as total_orders,
                    SUM(amount) as lifetime_value,
                    MAX(order_date) as last_order_date
                FROM gold.sales_enriched
                GROUP BY customer_id
                """
            }
        },
    )
    
    # Phase 5: ML Model Training
    train_model = DatabricksSubmitRunOperator(
        task_id='train_forecasting_model',
        databricks_conn_id='databricks_default',
        new_cluster=CLUSTER,
        notebook_task={
            "notebook_path": "/Workspace/ml/train_forecasting",
            "base_parameters": {
                "features": "sales_history,seasonality,trends",
                "target": "revenue"
            }
        },
    )
    
    # Phase 6: Generate Predictions
    predictions = DatabricksSubmitRunOperator(
        task_id='generate_predictions',
        databricks_conn_id='databricks_default',
        new_cluster=CLUSTER,
        notebook_task={
            "notebook_path": "/Workspace/ml/predict",
            "base_parameters": {
                "model": "sales_forecast",
                "horizon": "30"
            }
        },
    )
    
    # Phase 7: Export Results
    export_results = DatabricksSubmitRunOperator(
        task_id='export_to_powerbi',
        databricks_conn_id='databricks_default',
        new_cluster=CLUSTER,
        notebook_task={
            "notebook_path": "/Workspace/export/to_powerbi",
            "base_parameters": {
                "tables": "daily_sales_summary,customer_metrics"
            }
        },
    )
    
    def log_completion():
        """Log pipeline completion"""
        print("=" * 60)
        print("✅ Complete Databricks Pipeline Finished Successfully")
        print("=" * 60)
        return "success"
    
    complete = PythonOperator(
        task_id='log_completion',
        python_callable=log_completion
    )
    
    end = EmptyOperator(task_id='end')
    
    # Pipeline Flow
    start >> [ingest_sales, ingest_customers, ingest_products]
    [ingest_sales, ingest_customers, ingest_products] >> transform
    transform >> quality_checks
    quality_checks >> [daily_summary, customer_summary]
    [daily_summary, customer_summary] >> train_model
    train_model >> predictions
    predictions >> export_results
    export_results >> complete >> end
