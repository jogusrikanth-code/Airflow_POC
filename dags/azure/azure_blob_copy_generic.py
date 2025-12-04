"""
Simple Azure File Copy
=======================
Copies files from one Azure container to another.
Uses Airflow connection: azure_blob_default
"""
from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.providers.microsoft.azure.hooks.wasb import WasbHook
from datetime import datetime


def copy_files(**context):
    """Main function: Find files and copy them."""
    
    # Step 1: Get settings
    source = context['params']['source_container']
    target = context['params']['target_container']
    folder = context['params']['folder_path']
    
    # Step 2: Connect to Azure using Airflow connection
    hook = WasbHook(wasb_conn_id='azure_blob_default')
    client = hook.get_conn()
    
    # Step 3: Find files in source folder
    source_container = client.get_container_client(source)
    files = list(source_container.list_blobs(name_starts_with=folder))
    
    print(f"Found {len(files)} files to copy")
    
    # Step 4: Copy each file
    for blob in files:
        print(f"Copying: {blob.name}")
        data = client.get_blob_client(source, blob.name).download_blob().readall()
        client.get_blob_client(target, blob.name).upload_blob(data, overwrite=True)
        print(f"  ✓ Done")
    
    print(f"\n✓ Success! Copied {len(files)} files")


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

