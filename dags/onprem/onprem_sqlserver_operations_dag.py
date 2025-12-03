"""On-Prem SQL Server Operations DAG
=====================================
Demonstrates connecting to on-premises SQL Server.

Examples:
- Query data from SQL Server
- Export data to Azure Blob Storage
"""

from airflow import DAG
from airflow.operators.python import PythonOperator
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)


def query_sql_server(**context):
    """Query data from on-prem SQL Server."""
    from src.connectors import OnPremConnector
    
    # SQL Server configuration
    config = {
        'host': 'sql-server.company.local',
        'port': 1433,
        'database': 'SalesDB',
        'username': 'airflow_user',
        'password': 'password123'  # Better: use Airflow Connection
    }
    
    connector = OnPremConnector('sql_server', config)
    
    try:
        logger.info("Querying SQL Server...")
        
        query = """
        SELECT TOP 100
            OrderID,
            CustomerID,
            OrderDate,
            TotalAmount
        FROM Orders
        WHERE OrderDate >= DATEADD(day, -7, GETDATE())
        """
        
        data = connector.fetch_data(query)
        
        logger.info(f"✓ Retrieved {len(data)} orders")
        
        # Push to XCom for downstream tasks
        context['task_instance'].xcom_push(key='order_count', value=len(data))
        
        return {'rows': len(data), 'sample': data[:5] if data else []}
        
    finally:
        connector.close()


def export_to_azure(**context):
    """Export SQL Server data to Azure Blob Storage."""
    from src.connectors import OnPremConnector, get_azure_storage_connector
    import pandas as pd
    
    # Get SQL Server data
    sql_config = {
        'host': 'sql-server.company.local',
        'database': 'SalesDB',
        'username': 'airflow_user',
        'password': 'password123'
    }
    
    sql_connector = OnPremConnector('sql_server', sql_config)
    
    try:
        logger.info("Extracting data from SQL Server...")
        
        query = """
        SELECT *
        FROM Orders
        WHERE OrderDate >= DATEADD(day, -7, GETDATE())
        """
        
        data = sql_connector.fetch_data(query)
        logger.info(f"✓ Extracted {len(data)} rows")
        
        # Convert to DataFrame
        df = pd.DataFrame(data)
        
        # Upload to Azure
        azure = get_azure_storage_connector('azure_default')
        blob_name = f"exports/orders_{datetime.now().strftime('%Y%m%d')}.csv"
        
        logger.info(f"Uploading to Azure: {blob_name}")
        azure.upload_dataframe(df, 'exports', blob_name, format='csv')
        
        logger.info("✓ Data exported to Azure")
        
        return {'rows': len(data), 'blob': blob_name}
        
    finally:
        sql_connector.close()


# DAG definition
default_args = {
    'owner': 'airflow',
    'depends_on_past': False,
    'start_date': datetime(2024, 12, 1),
    'email_on_failure': False,
    'email_on_retry': False,
    'retries': 1,
    'retry_delay': timedelta(minutes=5),
}

with DAG(
    'onprem_sqlserver_operations',
    default_args=default_args,
    description='Query and export data from on-prem SQL Server',
    schedule='@daily',
    catchup=False,
    tags=['onprem', 'sql-server', 'export', 'example'],
) as dag:
    
    # Task 1: Query SQL Server
    query_data = PythonOperator(
        task_id='query_sql_server',
        python_callable=query_sql_server,
    )
    
    # Task 2: Export to Azure
    export_data = PythonOperator(
        task_id='export_to_azure',
        python_callable=export_to_azure,
    )
    
    # Run tasks sequentially
    query_data >> export_data
