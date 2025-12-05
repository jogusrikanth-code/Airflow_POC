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
    
    def copy_one_file(**context):
        """Copy a single file as a test"""
        from azure.storage.blob import BlobServiceClient
        from airflow.hooks.base import BaseHook
        
        print("=" * 60)
        print("Azure Blob Copy - Single File Test")
        print("=" * 60)
        
        # Get connection
        conn = BaseHook.get_connection('azure_blob_default')
        conn_str = f"DefaultEndpointsProtocol=https;AccountName={conn.host};AccountKey={conn.password};EndpointSuffix=core.windows.net"
        
        client = BlobServiceClient.from_connection_string(conn_str)
        container_client = client.get_container_client(CONTAINER)
        
        # List blobs and get the first actual file
        all_blobs = list(container_client.list_blobs(name_starts_with=SOURCE_FOLDER, max_results=5))
        
        # Find first non-folder blob
        source_blob = None
        for blob in all_blobs:
            if not blob.name.endswith('/') and blob.size > 0:
                source_blob = blob.name
                break
        
        if not source_blob:
            print("❌ No files found to copy")
            return {'status': 'no_files', 'copied': 0}
        
        # Extract just filename
        filename = source_blob.split('/')[-1]
        target_path = f"{TARGET_FOLDER}/{filename}"
        
        print(f"\n📁 Source: {source_blob}")
        print(f"📁 Target: {target_path}")
        print(f"📊 Size: {all_blobs[0].size} bytes")
        
        # Server-side copy
        source_url = f"https://{conn.host}.blob.core.windows.net/{CONTAINER}/{source_blob}"
        target_blob = container_client.get_blob_client(target_path)
        
        print(f"\n🔄 Starting server-side copy...")
        copy_result = target_blob.start_copy_from_url(source_url)
        
        print(f"✅ Copy initiated successfully!")
        print(f"   Copy ID: {copy_result.get('copy_id', 'N/A')}")
        
        print("\n" + "=" * 60)
        print(f"✅ File copied to {TARGET_FOLDER}/")
        print("=" * 60)
        
        return {'status': 'success', 'source': source_blob, 'target': target_path, 'copied': 1}
    
    copy_task = PythonOperator(
        task_id='copy_single_file',
        python_callable=copy_one_file,
    )
