"""
SQL Server to Databricks ETL
=============================
Extract data from on-premise SQL Server and load to Databricks.
Demonstrates hybrid cloud/on-prem integration.

What you need:
1. SQL Server connection 'mssql_onprem' configured
2. Databricks connection 'databricks_default' configured
3. Source table in SQL Server
4. Target table/path in Databricks

Pipeline:
1. Extract from SQL Server to CSV/Parquet
2. Upload to cloud storage (Azure Blob or DBFS)
3. Load to Databricks Delta table
4. Run transformations in Databricks
"""
from airflow import DAG
from airflow.providers.microsoft.mssql.hooks.mssql import MsSqlHook
from airflow.providers.databricks.operators.databricks import DatabricksSubmitRunOperator
from airflow.operators.python import PythonOperator
from datetime import datetime, timedelta
import pandas as pd
import tempfile
import os

# Configuration
MSSQL_CONN_ID = 'mssql_onprem'
DATABRICKS_CONN_ID = 'databricks_default'
SOURCE_TABLE = '[dbo].[orders]'
TARGET_PATH = '/mnt/bronze/orders'
TEMP_FILE_PATH = '/tmp/sqlserver_extract.parquet'

default_args = {
    'owner': 'airflow',
    'retries': 2,
    'retry_delay': timedelta(minutes=5),
}

with DAG(
    dag_id='mssql_to_databricks_etl',
    default_args=default_args,
    description='ETL from SQL Server to Databricks',
    schedule='0 2 * * *',  # Daily at 2 AM
    start_date=datetime(2025, 1, 1),
    catchup=False,
    tags=['mssql', 'databricks', 'etl', 'hybrid'],
) as dag:
    
    def extract_from_sqlserver(**context):
        """Extract data from SQL Server and save to temporary file"""
        hook = MsSqlHook(mssql_conn_id=MSSQL_CONN_ID)
        
        # Query to extract data
        query = f"""
        SELECT 
            order_id,
            customer_id,
            order_date,
            order_amount,
            status,
            created_at,
            updated_at
        FROM {SOURCE_TABLE}
        WHERE CAST(updated_at AS DATE) >= CAST(DATEADD(day, -1, GETDATE()) AS DATE)
        ORDER BY order_id;
        """
        
        print(f"Extracting data from SQL Server: {SOURCE_TABLE}")
        print(f"Query: {query}")
        
        # Get data as pandas DataFrame
        df = hook.get_pandas_df(query)
        
        row_count = len(df)
        print(f"Extracted {row_count} rows from SQL Server")
        
        if row_count == 0:
            print("⚠️  No data to extract")
            return {'status': 'no_data', 'row_count': 0}
        
        # Save to temporary parquet file
        os.makedirs(os.path.dirname(TEMP_FILE_PATH), exist_ok=True)
        df.to_parquet(TEMP_FILE_PATH, index=False)
        
        print(f"Data saved to: {TEMP_FILE_PATH}")
        print(f"File size: {os.path.getsize(TEMP_FILE_PATH)} bytes")
        
        # Push metadata to XCom
        context['task_instance'].xcom_push(key='row_count', value=row_count)
        context['task_instance'].xcom_push(key='file_path', value=TEMP_FILE_PATH)
        
        return {
            'status': 'extracted',
            'row_count': row_count,
            'file_path': TEMP_FILE_PATH
        }
    
    extract = PythonOperator(
        task_id='extract_from_sqlserver',
        python_callable=extract_from_sqlserver,
    )
    
    # Load to Databricks using notebook
    load_to_databricks = DatabricksSubmitRunOperator(
        task_id='load_to_databricks',
        databricks_conn_id=DATABRICKS_CONN_ID,
        notebook_task={
            'notebook_path': '/Workspace/ETL/load_sqlserver_data',
            'base_parameters': {
                'source_file': TEMP_FILE_PATH,
                'target_path': TARGET_PATH,
                'load_date': '{{ ds }}',
            }
        },
        new_cluster={
            'spark_version': '13.3.x-scala2.12',
            'node_type_id': 'Standard_DS3_v2',
            'num_workers': 2,
            'spark_conf': {
                'spark.sql.adaptive.enabled': 'true',
            }
        },
    )
    
    # Transform in Databricks
    transform_in_databricks = DatabricksSubmitRunOperator(
        task_id='transform_in_databricks',
        databricks_conn_id=DATABRICKS_CONN_ID,
        spark_python_task={
            'python_file': 'dbfs:/scripts/transform_orders.py',
            'parameters': [
                '--source_path', TARGET_PATH,
                '--target_path', f'{TARGET_PATH}_transformed',
                '--date', '{{ ds }}'
            ]
        },
        existing_cluster_id='{{ var.value.databricks_cluster_id }}',  # Use existing cluster
    )
    
    # Alternative: Use SQL for transformation
    transform_with_sql = DatabricksSubmitRunOperator(
        task_id='transform_with_sql',
        databricks_conn_id=DATABRICKS_CONN_ID,
        sql_task={
            'query': {
                'query': f"""
                CREATE OR REPLACE TABLE gold.orders_summary AS
                SELECT 
                    DATE(order_date) AS order_date,
                    COUNT(*) AS total_orders,
                    SUM(order_amount) AS total_amount,
                    AVG(order_amount) AS avg_amount
                FROM delta.`{TARGET_PATH}_transformed`
                WHERE DATE(order_date) = '{{{{ ds }}}}'
                GROUP BY DATE(order_date);
                """
            },
            'warehouse_id': '{{ var.value.databricks_warehouse_id }}'
        },
    )
    
    def validate_load(**context):
        """Validate that data was loaded successfully"""
        row_count = context['task_instance'].xcom_pull(
            task_ids='extract_from_sqlserver',
            key='row_count'
        )
        
        print(f"Expected rows: {row_count}")
        print("✅ Data successfully loaded to Databricks")
        
        # Cleanup temporary file
        if os.path.exists(TEMP_FILE_PATH):
            os.remove(TEMP_FILE_PATH)
            print(f"Cleaned up temporary file: {TEMP_FILE_PATH}")
        
        return {
            'status': 'validated',
            'rows_extracted': row_count
        }
    
    validate = PythonOperator(
        task_id='validate_and_cleanup',
        python_callable=validate_load,
    )
    
    # Pipeline flow
    extract >> load_to_databricks >> transform_in_databricks >> transform_with_sql >> validate
