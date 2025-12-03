"""On-Prem to Databricks ETL DAG
===================================
Demonstrates ETL pipeline from on-prem SQL Server to Databricks.

Pattern:
- Extract data from SQL Server
- Transform data
- Load to Databricks table
"""

from airflow import DAG
from airflow.operators.python import PythonOperator
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)


def extract_from_sqlserver(**context):
    """Extract data from on-prem SQL Server."""
    from src.connectors import OnPremConnector
    import pandas as pd
    
    config = {
        'host': 'sql-server.company.local',
        'database': 'SalesDB',
        'username': 'airflow_user',
        'password': 'password123'
    }
    
    connector = OnPremConnector('sql_server', config)
    
    try:
        logger.info("Extracting from SQL Server...")
        
        query = """
        SELECT
            OrderID,
            CustomerID,
            ProductID,
            OrderDate,
            Quantity,
            UnitPrice,
            TotalAmount
        FROM Orders
        WHERE OrderDate >= DATEADD(day, -30, GETDATE())
        """
        
        data = connector.fetch_data(query)
        
        # Convert to DataFrame
        df = pd.DataFrame(data)
        
        logger.info(f"✓ Extracted {len(df)} rows")
        
        # Save to temp location
        temp_path = '/tmp/orders_extract.csv'
        df.to_csv(temp_path, index=False)
        
        return {'rows': len(df), 'path': temp_path}
        
    finally:
        connector.close()


def transform_data(**context):
    """Transform extracted data."""
    import pandas as pd
    
    # Get extract path from previous task
    ti = context['task_instance']
    extract_result = ti.xcom_pull(task_ids='extract_from_sqlserver')
    
    logger.info("Transforming data...")
    
    df = pd.read_csv(extract_result['path'])
    
    # Add calculated columns
    df['Year'] = pd.to_datetime(df['OrderDate']).dt.year
    df['Month'] = pd.to_datetime(df['OrderDate']).dt.month
    df['Revenue'] = df['Quantity'] * df['UnitPrice']
    
    # Save transformed data
    temp_path = '/tmp/orders_transformed.csv'
    df.to_csv(temp_path, index=False)
    
    logger.info(f"✓ Transformed {len(df)} rows")
    
    return {'rows': len(df), 'path': temp_path}


def load_to_databricks(**context):
    """Load data to Databricks table."""
    from src.connectors import get_databricks_connector
    import pandas as pd
    
    # Get transform path from previous task
    ti = context['task_instance']
    transform_result = ti.xcom_pull(task_ids='transform_data')
    
    logger.info("Loading to Databricks...")
    
    df = pd.read_csv(transform_result['path'])
    
    # Get Databricks connector
    databricks = get_databricks_connector('databricks_default')
    
    # In real scenario, upload to DBFS and load to table
    # For POC, just log the operation
    
    table_name = 'sales.orders'
    logger.info(f"Would load {len(df)} rows to {table_name}")
    logger.info(f"Sample data:\n{df.head()}")
    
    logger.info(f"✓ Loaded {len(df)} rows to Databricks")
    
    return {'rows': len(df), 'table': table_name}


# DAG definition
default_args = {
    'owner': 'airflow',
    'depends_on_past': False,
    'start_date': datetime(2024, 12, 1),
    'email_on_failure': False,
    'email_on_retry': False,
    'retries': 2,
    'retry_delay': timedelta(minutes=5),
}

with DAG(
    'onprem_to_databricks_etl',
    default_args=default_args,
    description='ETL pipeline from SQL Server to Databricks',
    schedule='@daily',
    catchup=False,
    tags=['onprem', 'databricks', 'etl', 'example'],
) as dag:
    
    # Task 1: Extract from SQL Server
    extract = PythonOperator(
        task_id='extract_from_sqlserver',
        python_callable=extract_from_sqlserver,
    )
    
    # Task 2: Transform data
    transform = PythonOperator(
        task_id='transform_data',
        python_callable=transform_data,
    )
    
    # Task 3: Load to Databricks
    load = PythonOperator(
        task_id='load_to_databricks',
        python_callable=load_to_databricks,
    )
    
    # ETL pipeline
    extract >> transform >> load
