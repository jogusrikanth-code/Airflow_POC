"""
Simple Azure File Copy
=======================
Copies files from one Azure container to another.
Uses Airflow connection: azure_blob_default
"""
from airflow import DAG
from airflow.operators.python import PythonOperator
from datetime import datetime


def copy_files(**context):
    """Main function: Find files and copy them."""
    from azure.storage.blob import BlobServiceClient
    from airflow.hooks.base import BaseHook
    import traceback
    
    try:
        # Step 1: Get settings
        source = context['params']['source_container']
        target = context['params']['target_container']
        folder = context['params']['folder_path']
        
        print(f"Starting copy operation:")
        print(f"  Source container: {source}")
        print(f"  Target container: {target}")
        print(f"  Folder path: {folder}")
        
        # Step 2: Get Azure credentials from Airflow connection
        print("Getting Azure credentials from connection 'azure_blob_default'...")
        conn = BaseHook.get_connection('azure_blob_default')
        account_name = conn.login
        account_key = conn.password
        
        print(f"  Account name: {account_name}")
        print(f"  Key length: {len(account_key) if account_key else 0} characters")
        
        # Step 3: Connect to Azure
        print("Connecting to Azure Blob Storage...")
        client = BlobServiceClient(
            account_url=f"https://{account_name}.blob.core.windows.net",
            credential=account_key
        )
        
        # Step 4: Find files in source folder
        print(f"Listing blobs in source container '{source}' with prefix '{folder}'...")
        source_container = client.get_container_client(source)
        files = list(source_container.list_blobs(name_starts_with=folder))
        
        print(f"Found {len(files)} files to copy")
        
        if len(files) == 0:
            print("⚠️ No files found matching the criteria")
            return
        
        # Step 5: Copy each file (server-side copy - no data flows through Airflow)
        target_container = client.get_container_client(target)
        copied_count = 0
        total_bytes = 0
        
        for i, blob in enumerate(files, 1):
            print(f"[{i}/{len(files)}] Copying: {blob.name} ({blob.size:,} bytes)")
            
            # Build source URL for server-side copy
            source_url = f"{client.account_url}/{source}/{blob.name}"
            
            # Get target blob client
            target_blob = target_container.get_blob_client(blob.name)
            
            # Start server-side copy (Azure handles the transfer internally)
            copy_result = target_blob.start_copy_from_url(source_url)
            
            print(f"  ✓ Copy initiated (Azure is handling the transfer)")
            
            copied_count += 1
            total_bytes += blob.size
        
        print(f"\n✅ Success! Initiated {copied_count} file copies")
        print(f"   Total size: {total_bytes:,} bytes ({total_bytes/1024/1024:.2f} MB)")
        print(f"   Note: Copies are handled server-side by Azure (no load on Airflow)")
        
        return {
            'files_copied': copied_count,
            'total_bytes': total_bytes,
            'source_container': source,
            'target_container': target
        }
        
    except Exception as e:
        print(f"\n❌ Error occurred: {type(e).__name__}: {str(e)}")
        print("\nFull traceback:")
        traceback.print_exc()
        raise


# Create DAG
with DAG(
    dag_id='azure_blob_copy',
    start_date=datetime(2024, 12, 1),
    schedule=None,  # Manual trigger only
    catchup=False,
    tags=['azure', 'simple'],
    params={
        'source_container': 'sg-analytics-raw',
        'target_container': 'airflow',
        'folder_path': 'seasonal_buy/2025-10-13/'
    }
) as dag:
    
    # Single task: copy files
    PythonOperator(
        task_id='copy_files',
        python_callable=copy_files
    )

