"""
Copy Files from Azure Blob Storage
===================================
Copies files between folders in Azure Blob Storage.

Connection: azure_blob_default
Container: sg-analytics-raw
Source: seasonal_buy/2025-10-12/
Target: Airflow/test/

Setup Required:
1. Configure 'azure_blob_default' connection in Airflow UI
2. Update SOURCE_FOLDER and TARGET_FOLDER if needed
"""
from airflow import DAG
from airflow.operators.python import PythonOperator
from datetime import datetime

# Configuration
CONTAINER = 'sg-analytics-raw'
SOURCE_FOLDER = 'seasonal_buy/2025-10-12'  # UPDATE if needed
TARGET_FOLDER = 'Airflow/test'            # UPDATE if needed

# DAG Definition
with DAG(
    dag_id='azure_blob_copy_files',
    description='Copy files between Azure Blob folders',
    schedule=None,  # Run manually
    start_date=datetime(2025, 1, 1),
    catchup=False,
    tags=['azure', 'file-copy'],
) as dag:
    
    def copy_all_files(**context):
        """Copy all files from source to target folder"""
        from azure.storage.blob import BlobServiceClient
        from airflow.hooks.base import BaseHook
        
        # Step 1: Connect to Azure
        conn = BaseHook.get_connection('azure_blob_default')
        conn_str = f"DefaultEndpointsProtocol=https;AccountName={conn.host};AccountKey={conn.password};EndpointSuffix=core.windows.net"
        client = BlobServiceClient.from_connection_string(conn_str)
        container = client.get_container_client(CONTAINER)
        
        # Step 2: List files in source folder
        print(f"\nSource: {SOURCE_FOLDER}")
        blobs = [b for b in container.list_blobs(name_starts_with=SOURCE_FOLDER) 
                 if not b.name.endswith('/') and b.size > 0]
        
        if not blobs:
            print("No files found")
            return {'status': 'no_files', 'copied': 0}
        
        print(f"Found {len(blobs)} file(s)\n")
        
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
