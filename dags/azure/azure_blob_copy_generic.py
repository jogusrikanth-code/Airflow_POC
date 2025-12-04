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
        
        # Step 5: Copy each file
        for i, blob in enumerate(files, 1):
            print(f"[{i}/{len(files)}] Copying: {blob.name}")
            data = client.get_blob_client(source, blob.name).download_blob().readall()
            client.get_blob_client(target, blob.name).upload_blob(data, overwrite=True)
            print(f"  ✓ Done ({len(data)} bytes)")
        
        print(f"\n✅ Success! Copied {len(files)} files")
        
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

