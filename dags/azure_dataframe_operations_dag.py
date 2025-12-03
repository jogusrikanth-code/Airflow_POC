"""
"""Azure DataFrame Operations DAG
==============================
Demonstrates working with DataFrames and Azure Blob Storage.

Examples:
- Upload DataFrame to blob storage
- Download and transform DataFrame
"""

from airflow import DAG
from airflow.operators.python import PythonOperator
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)


def upload_dataframe_to_blob(**context):
    """Upload a DataFrame to blob storage in CSV format."""
    from src.connectors import get_azure_storage_connector
    import pandas as pd
    
    azure = get_azure_storage_connector('azure_default')
    
    # Create sample DataFrame
    df = pd.DataFrame({
        'order_id': [1001, 1002, 1003, 1004],
        'product': ['Widget A', 'Widget B', 'Widget A', 'Widget C'],
        'quantity': [5, 3, 8, 2],
        'price': [29.99, 49.99, 29.99, 19.99]
    })
    
    container = 'processed'
    blob_name = 'sales/orders_summary.csv'
    
    logger.info(f"Uploading DataFrame ({len(df)} rows) to {container}/{blob_name}")
    
    # Upload as CSV
    azure.upload_dataframe(df, container, blob_name, format='csv')
    
    logger.info(f"✓ Successfully uploaded DataFrame to blob storage")
    
    return {'rows': len(df), 'format': 'csv', 'blob': blob_name}


def download_and_transform(**context):
    """Download DataFrame from blob and perform transformation."""
    from src.connectors import get_azure_storage_connector
    import pandas as pd
    
    azure = get_azure_storage_connector('azure_default')
    
    container = 'raw'
    blob_name = 'sales/sample_source_a.csv'
    
    logger.info(f"Downloading DataFrame from {container}/{blob_name}")
    
    # Download as DataFrame
    df = azure.download_dataframe(container, blob_name, format='csv')
    
    logger.info(f"Downloaded {len(df)} rows with columns: {list(df.columns)}")
    
    # Perform transformation (example: add calculated column)
    if 'amount' in df.columns and 'quantity' in df.columns:
        df['total_value'] = df['amount'] * df['quantity']
        logger.info("Added calculated column: total_value")
    
    # Upload transformed data
    output_blob = 'sales/transformed_data.csv'
    azure.upload_dataframe(df, 'processed', output_blob, format='csv')
    
    logger.info(f"✓ Uploaded transformed DataFrame to processed/{output_blob}")
    
    return {'rows': len(df), 'columns': list(df.columns)}





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
    'azure_dataframe_operations',
    default_args=default_args,
    description='DataFrame operations with Azure Blob Storage',
    schedule='@daily',
    catchup=False,
    tags=['azure', 'blob', 'dataframe', 'pandas', 'example'],
) as dag:
    
    # Task 1: Upload DataFrame to blob
    upload_df = PythonOperator(
        task_id='upload_dataframe_to_blob',
        python_callable=upload_dataframe_to_blob,
    )
    
    # Task 2: Download and transform
    download_transform = PythonOperator(
        task_id='download_and_transform',
        python_callable=download_and_transform,
    )
    
    # Tasks run independently
    [upload_df, download_transform]
