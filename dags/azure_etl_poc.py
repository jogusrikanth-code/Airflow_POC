"""
Azure Blob Storage File Copy POC
==================================
Copy a single test file from seasonal_buy to Airflow folder.
Uses server-side copy (no data transfer through Airflow).

Storage: sgbilakehousestoragedev
Container: sg-analytics-raw
Source: seasonal_buy/2025-10-12/
Target: Airflow/test/

Connection: azure_blob_default

Note: Run test_azure_connection DAG first to verify connection.
"""
from airflow import DAG
from airflow.operators.python import PythonOperator
from datetime import datetime, timedelta

default_args = {
    'owner': 'airflow',
    'retries': 1,
    'retry_delay': timedelta(minutes=2),
}

CONTAINER = 'sg-analytics-raw'
SOURCE_FOLDER = 'seasonal_buy/2025-10-12'
TARGET_FOLDER = 'Airflow/test'

with DAG(
    'azure_etl_poc',
    default_args=default_args,
    description='Copy one test file from seasonal_buy to Airflow folder',
    schedule=None,
    start_date=datetime(2025, 1, 1),
    catchup=False,
    tags=['azure', 'poc', 'file-copy'],
) as dag:
    
    def copy_all_files(**context):
        """Copy all files from source folder to target folder"""
        from azure.storage.blob import BlobServiceClient
        from airflow.hooks.base import BaseHook
        
        print("=" * 60)
        print("Azure Blob Copy - Multiple Files")
        print("=" * 60)
        
        # Get connection
        conn = BaseHook.get_connection('azure_blob_default')
        conn_str = f"DefaultEndpointsProtocol=https;AccountName={conn.host};AccountKey={conn.password};EndpointSuffix=core.windows.net"
        
        client = BlobServiceClient.from_connection_string(conn_str)
        container_client = client.get_container_client(CONTAINER)
        
        # List all blobs in source folder
        print(f"\n📁 Source folder: {SOURCE_FOLDER}")
        blob_list = container_client.list_blobs(name_starts_with=SOURCE_FOLDER)
        
        # Get all non-folder blobs
        source_blobs = []
        for blob in blob_list:
            if not blob.name.endswith('/') and blob.size > 0:
                source_blobs.append(blob)
        
        if not source_blobs:
            print("❌ No files found to copy")
            return {'status': 'no_files', 'copied': 0}
        
        print(f"📊 Found {len(source_blobs)} file(s) to copy\n")
        
        # Copy all files
        copied_count = 0
        for source_blob in source_blobs:
            try:
                # Extract just filename
                filename = source_blob.name.split('/')[-1]
                target_path = f"{TARGET_FOLDER}/{filename}"
                
                # Server-side copy
                source_url = f"https://{conn.host}.blob.core.windows.net/{CONTAINER}/{source_blob.name}"
                target_blob_client = container_client.get_blob_client(target_path)
                
                copy_result = target_blob_client.start_copy_from_url(source_url)
                
                print(f"✅ {filename} ({source_blob.size} bytes)")
                print(f"   → {target_path}")
                print(f"   Copy ID: {copy_result.get('copy_id', 'N/A')}\n")
                copied_count += 1
                
            except Exception as e:
                print(f"❌ Failed to copy {source_blob.name}: {str(e)}\n")
        
        print("=" * 60)
        print(f"✅ Successfully copied {copied_count}/{len(source_blobs)} files to {TARGET_FOLDER}/")
        print("=" * 60)
        
        return {'status': 'success', 'total_files': len(source_blobs), 'copied': copied_count}
    
    copy_task = PythonOperator(
        task_id='copy_single_file',
        python_callable=copy_all_files,
    )
