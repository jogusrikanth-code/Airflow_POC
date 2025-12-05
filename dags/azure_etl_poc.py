"""
Azure Blob Storage File Copy POC
==================================
Simple POC to copy files from seasonal_buy to Airflow folder.
Uses server-side copy (no data transfer through Airflow).

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
    description='Copy files from seasonal_buy to Airflow folder (server-side)',

    schedule=None,
    start_date=datetime(2025, 1, 1),
    catchup=False,
    tags=['azure', 'poc', 'file-copy'],
) as dag:
    
    def copy_files(**context):
        """Copy files from source to target folder using server-side copy"""
        from azure.storage.blob import BlobServiceClient
        from airflow.hooks.base import BaseHook
        
        # Get connection
        conn = BaseHook.get_connection('azure_blob_default')
        conn_str = f"DefaultEndpointsProtocol=https;AccountName={conn.host};AccountKey={conn.password};EndpointSuffix=core.windows.net"
        
        client = BlobServiceClient.from_connection_string(conn_str)
        container_client = client.get_container_client(CONTAINER)
        
        # List files in source folder (exclude folder markers)
        all_blobs = list(container_client.list_blobs(name_starts_with=SOURCE_FOLDER))
        print(f"DEBUG: Total blobs found: {len(all_blobs)}")
        for blob in all_blobs[:5]:  # Show first 5 for debugging
            print(f"DEBUG: Blob: {blob.name}")
        
        source_blobs = [blob.name for blob in all_blobs if not blob.name.endswith('/')]
        
        print(f"Found {len(source_blobs)} files in {SOURCE_FOLDER}")
        
        # Copy each file (server-side operation - no data transfer through Airflow)
        copied_count = 0
        for source_path in source_blobs:
            # Preserve the folder structure or flatten - here we flatten to target folder
            filename = source_path.replace(SOURCE_FOLDER + '/', '')
            target_path = f"{TARGET_FOLDER}/{filename}"
            
            print(f"Copying: {filename}")
            
            # Server-side copy using copy_blob (Azure handles the copy internally)
            source_url = f"https://{conn.host}.blob.core.windows.net/{CONTAINER}/{source_path}"
            target_blob = container_client.get_blob_client(target_path)
            target_blob.start_copy_from_url(source_url)
            
            copied_count += 1
        
        print(f"✓ Copied {copied_count} files to {TARGET_FOLDER} (server-side copy)")
        return {'copied_count': copied_count}
    
    copy_task = PythonOperator(
        task_id='copy_files',
        python_callable=copy_files,
    )
