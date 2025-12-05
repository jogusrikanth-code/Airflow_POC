"""
Simple Azure File Copy
=======================
Copies files between folders in Azure Blob Storage.

What you need:
- Connection 'azure_blob_default' configured in Airflow
- Source and target folders in same container

How to use:
1. Update CONFIG section below (lines 18-20)
2. Enable the DAG and run
"""
from airflow import DAG
from airflow.operators.python import PythonOperator
from datetime import datetime

# Configuration - UPDATE THESE
CONFIG = {
    "container": "sg-analytics-raw",
    "source_folder": "seasonal_buy/2025-10-12",  # Where to copy from
    "target_folder": "Airflow/test"              # Where to copy to
}

with DAG(
    dag_id='simple_azure_copy',
    description='Copy files between Azure Blob folders',
    schedule=None,  # Run manually
    start_date=datetime(2025, 1, 1),
    catchup=False,
    tags=['azure', 'file-copy', 'simple'],
) as dag:
    
    def copy_files():
        """Copy all files from source to target"""
        from azure.storage.blob import BlobServiceClient
        from airflow.hooks.base import BaseHook
        
        # Connect to Azure
        conn = BaseHook.get_connection('azure_blob_default')
        conn_str = f"DefaultEndpointsProtocol=https;AccountName={conn.host};AccountKey={conn.password};EndpointSuffix=core.windows.net"
        
        client = BlobServiceClient.from_connection_string(conn_str)
        container = client.get_container_client(CONFIG["container"])
        
        # List files
        blobs = [b for b in container.list_blobs(name_starts_with=CONFIG["source_folder"]) 
                 if not b.name.endswith('/') and b.size > 0]
        
        if not blobs:
            print("No files found to copy")
            return {'copied': 0}
        
        print(f"\nFound {len(blobs)} file(s) to copy")
        
        # Copy each file
        copied = 0
        for blob in blobs:
            filename = blob.name.split('/')[-1]
            target = f"{CONFIG['target_folder']}/{filename}"
            
            # Server-side copy (fast)
            source_url = f"https://{conn.host}.blob.core.windows.net/{CONFIG['container']}/{blob.name}"
            target_blob = container.get_blob_client(target)
            target_blob.start_copy_from_url(source_url)
            
            print(f"✓ Copied: {filename}")
            copied += 1
        
        print(f"\n✅ Copied {copied}/{len(blobs)} files")
        return {'copied': copied, 'total': len(blobs)}
    
    # Single task
    copy_task = PythonOperator(
        task_id='copy_all_files',
        python_callable=copy_files,
    )
