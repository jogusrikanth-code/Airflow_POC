"""Copy files between Azure containers"""
from airflow import DAG
from airflow.operators.python import PythonOperator
from datetime import datetime
import sys
sys.path.insert(0, '/opt/airflow/dags/repo')
from src.connectors.azure_connector import AZURE_STORAGE_ACCOUNT, AZURE_STORAGE_KEY

def copy_files(**context):
    """Copy all files from source to target folder."""
    from azure.storage.blob import BlobServiceClient
    
    source = context['params']['source_container']
    target = context['params']['target_container']
    folder = context['params']['folder_path']
    
    client = BlobServiceClient(
        account_url=f"https://{AZURE_STORAGE_ACCOUNT}.blob.core.windows.net",
        credential=AZURE_STORAGE_KEY
    )
    
    source_container = client.get_container_client(source)
    files = [blob.name for blob in source_container.list_blobs(name_starts_with=folder)]
    
    print(f"Copying {len(files)} files from {source}/{folder} to {target}/{folder}")
    
    for file in files:
        source_blob = client.get_blob_client(source, file)
        data = source_blob.download_blob().readall()
        target_blob = client.get_blob_client(target, file)
        target_blob.upload_blob(data, overwrite=True)
        print(f"✓ {file}")
    
    print(f"Done! Copied {len(files)} files")

with DAG(
    'azure_blob_copy_generic',
    start_date=datetime(2024, 12, 1),
    schedule=None,
    catchup=False,
    tags=['azure'],
    params={
        'source_container': 'sg-analytics-raw',
        'target_container': 'airflow',
        'folder_path': 'seasonal_buy/2025-10-13/'
    }
) as dag:
    PythonOperator(task_id='copy_files', python_callable=copy_files)
