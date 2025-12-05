"""
Azure Blob Storage ETL POC
==========================
Proof of concept for Azure integration:
- Extract data from Azure Blob Storage
- Process with server-side (Blob) operations
- Load results back to Azure

Connection required: azure_blob_default
"""
from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.providers.microsoft.azure.operators.blob import AzureBlobStorageUploadOperator
from airflow.providers.microsoft.azure.operators.blob import AzureBlobStorageDownloadOperator
from datetime import datetime, timedelta

default_args = {
    'owner': 'airflow',
    'retries': 1,
    'retry_delay': timedelta(minutes=5),
}

with DAG(
    'azure_etl_poc',
    default_args=default_args,
    description='Azure Blob Storage ETL POC',
    schedule_interval=None,
    start_date=datetime(2025, 1, 1),
    catchup=False,
    tags=['azure', 'poc', 'etl'],
) as dag:
    
    def extract_from_blob(**context):
        """Extract data from Azure Blob Storage"""
        from azure.storage.blob import BlobServiceClient
        from airflow.hooks.base import BaseHook
        
        # Get connection
        conn = BaseHook.get_connection('azure_blob_default')
        conn_str = f"DefaultEndpointsProtocol=https;AccountName={conn.host};AccountKey={conn.password};EndpointSuffix=core.windows.net"
        
        client = BlobServiceClient.from_connection_string(conn_str)
        container_client = client.get_container_client('data-raw')
        
        # List blobs
        blobs = list(container_client.list_blobs())
        print(f"Found {len(blobs)} blobs in data-raw container")
        
        context['task_instance'].xcom_push(key='blob_count', value=len(blobs))
        return {'status': 'extracted', 'blob_count': len(blobs)}
    
    def process_data(**context):
        """Process data (could involve Azure Data Lake, Databricks, etc.)"""
        blob_count = context['task_instance'].xcom_pull(task_ids='extract', key='blob_count')
        print(f"Processing data from {blob_count} blobs")
        
        # Simulate processing
        processed_count = blob_count * 2
        context['task_instance'].xcom_push(key='processed_count', value=processed_count)
        return {'status': 'processed', 'records': processed_count}
    
    def load_to_blob(**context):
        """Load processed data back to Azure Blob Storage"""
        from azure.storage.blob import BlobServiceClient
        from airflow.hooks.base import BaseHook
        
        processed_count = context['task_instance'].xcom_pull(task_ids='process', key='processed_count')
        
        # Get connection
        conn = BaseHook.get_connection('azure_blob_default')
        conn_str = f"DefaultEndpointsProtocol=https;AccountName={conn.host};AccountKey={conn.password};EndpointSuffix=core.windows.net"
        
        client = BlobServiceClient.from_connection_string(conn_str)
        container_client = client.get_container_client('data-processed')
        
        # Create container if not exists (simulation)
        print(f"Loading {processed_count} processed records to data-processed container")
        
        # Upload metadata
        blob_client = container_client.get_blob_client(f"metadata_{datetime.now().isoformat()}.txt")
        blob_client.upload_blob(f"Processed {processed_count} records\n")
        
        return {'status': 'loaded', 'processed_records': processed_count}
    
    # Tasks
    extract = PythonOperator(
        task_id='extract',
        python_callable=extract_from_blob,
        provide_context=True,
    )
    
    process = PythonOperator(
        task_id='process',
        python_callable=process_data,
        provide_context=True,
    )
    
    load = PythonOperator(
        task_id='load',
        python_callable=load_to_blob,
        provide_context=True,
    )
    
    # Pipeline
    extract >> process >> load
