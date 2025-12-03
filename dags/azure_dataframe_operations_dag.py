"""
Azure DataFrame Operations DAG
==============================
Demonstrates working with DataFrames and Azure Blob Storage.

Examples:
- Upload DataFrame in different formats (CSV, Parquet)
- Download DataFrame from blob and transform
- Convert between formats in blob storage
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


def convert_csv_to_parquet(**context):
    """Download CSV from blob, convert to Parquet, upload back."""
    from src.connectors import get_azure_storage_connector
    import pandas as pd
    
    azure = get_azure_storage_connector('azure_default')
    
    # Download CSV
    container = 'processed'
    csv_blob = 'sales/orders_summary.csv'
    
    logger.info(f"Downloading CSV from {container}/{csv_blob}")
    df = azure.download_dataframe(container, csv_blob, format='csv')
    
    # Upload as Parquet
    parquet_blob = 'sales/orders_summary.parquet'
    logger.info(f"Converting to Parquet and uploading to {container}/{parquet_blob}")
    
    azure.upload_dataframe(df, container, parquet_blob, format='parquet')
    
    logger.info(f"✓ Successfully converted CSV to Parquet ({len(df)} rows)")
    
    return {
        'source': csv_blob,
        'destination': parquet_blob,
        'rows': len(df),
        'format': 'parquet'
    }


def aggregate_and_upload(**context):
    """Aggregate data from multiple blobs and upload summary."""
    from src.connectors import get_azure_storage_connector
    import pandas as pd
    
    azure = get_azure_storage_connector('azure_default')
    
    container = 'raw'
    prefix = 'sales/'
    
    logger.info(f"Looking for CSV files in {container}/{prefix}")
    
    # List all CSV files
    blobs = [b for b in azure.list_blobs(container, prefix) if b.endswith('.csv')]
    logger.info(f"Found {len(blobs)} CSV files")
    
    # Download and combine
    all_data = []
    for blob in blobs[:3]:  # Limit to first 3 files for demo
        logger.info(f"Reading {blob}...")
        df = azure.download_dataframe(container, blob, format='csv')
        all_data.append(df)
    
    # Combine and aggregate
    combined = pd.concat(all_data, ignore_index=True)
    logger.info(f"Combined {len(combined)} total rows from {len(all_data)} files")
    
    # Upload aggregated data
    output_blob = 'sales/aggregated_summary.csv'
    azure.upload_dataframe(combined, 'processed', output_blob, format='csv')
    
    logger.info(f"✓ Uploaded aggregated data to processed/{output_blob}")
    
    return {
        'source_files': len(all_data),
        'total_rows': len(combined),
        'output': output_blob
    }


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
    
    # Task 3: Convert CSV to Parquet
    convert_format = PythonOperator(
        task_id='convert_csv_to_parquet',
        python_callable=convert_csv_to_parquet,
    )
    
    # Task 4: Aggregate from multiple files
    aggregate = PythonOperator(
        task_id='aggregate_and_upload',
        python_callable=aggregate_and_upload,
    )
    
    # Define dependencies
    upload_df >> convert_format
    download_transform >> aggregate
