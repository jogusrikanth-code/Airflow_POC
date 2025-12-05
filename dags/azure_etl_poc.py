"""
Azure Blob Storage File Move POC
==================================
Simple POC to move files from seasonal_buy to Airflow folder.

Storage: sgbilakehousestoragedev
Container: sg-analytics-raw
Source: seasonal_buy/2025-10-12/
Target: Airflow/

Connection: azure_blob_default
"""
from airflow import DAG
from airflow.operators.python import PythonOperator
from datetime import datetime, timedelta

default_args = {
    'owner': 'airflow',
    'retries': 1,
    'retry_delay': timedelta(minutes=5),
}

CONTAINER = 'sg-analytics-raw'
SOURCE_FOLDER = 'seasonal_buy/2025-10-12'
TARGET_FOLDER = 'Airflow'

with DAG(
    'azure_etl_poc',
    default_args=default_args,
    description='Move files from seasonal_buy to Airflow folder',
    schedule_interval=None,
    start_date=datetime(2025, 1, 1),
    catchup=False,
    tags=['azure', 'poc', 'file-move'],
) as dag:
    
    def move_files(**context):
        """Move files from source to target folder"""
        from azure.storage.blob import BlobServiceClient
        from airflow.hooks.base import BaseHook
        
        # Get connection
        conn = BaseHook.get_connection('azure_blob_default')
        conn_str = f"DefaultEndpointsProtocol=https;AccountName={conn.host};AccountKey={conn.password};EndpointSuffix=core.windows.net"
        
        client = BlobServiceClient.from_connection_string(conn_str)
        container_client = client.get_container_client(CONTAINER)
        
        # List files in source folder
        source_blobs = [blob.name for blob in container_client.list_blobs(name_starts_with=SOURCE_FOLDER) 
                       if blob.name != SOURCE_FOLDER + '/']
        
        print(f"Found {len(source_blobs)} files in {SOURCE_FOLDER}")
        
        # Move each file
        moved_count = 0
        for source_path in source_blobs:
            filename = source_path.split('/')[-1]
            target_path = f"{TARGET_FOLDER}/{filename}"
            
            print(f"Moving: {filename}")
            
            # Download and upload (move)
            source_blob = container_client.get_blob_client(source_path)
            data = source_blob.download_blob().readall()
            
            target_blob = container_client.get_blob_client(target_path)
            target_blob.upload_blob(data, overwrite=True)
            
            source_blob.delete_blob()
            moved_count += 1
        
        print(f"✓ Moved {moved_count} files to {TARGET_FOLDER}")
        return {'moved_count': moved_count}
    
    move_task = PythonOperator(
        task_id='move_files',
        python_callable=move_files,
    )
