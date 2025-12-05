"""
Azure Blob Storage ETL POC
==========================
Move files from seasonal_buy folder to Airflow folder in Azure Blob Storage.

Storage Account: sgbilakehousestoragedev
Source: sg-analytics-raw/seasonal_buy/2025-10-12/
Target: sg-analytics-raw/Airflow/

Connection required: azure_blob_default
"""
from airflow import DAG
from airflow.operators.python import PythonOperator
from datetime import datetime, timedelta

default_args = {
    'owner': 'airflow',
    'retries': 1,
    'retry_delay': timedelta(minutes=5),
}

# Configuration
STORAGE_ACCOUNT = 'sgbilakehousestoragedev'
CONTAINER = 'sg-analytics-raw'
SOURCE_FOLDER = 'seasonal_buy/2025-10-12'
TARGET_FOLDER = 'Airflow'

with DAG(
    'azure_etl_poc',
    default_args=default_args,
    description='Move files from seasonal_buy to Airflow folder in Azure Blob Storage',
    schedule_interval=None,
    start_date=datetime(2025, 1, 1),
    catchup=False,
    tags=['azure', 'poc', 'etl', 'file-move'],
) as dag:
    
    def list_source_files(**context):
        """List all files in seasonal_buy/2025-10-12 folder"""
        from azure.storage.blob import BlobServiceClient
        from airflow.hooks.base import BaseHook
        
        try:
            # Get connection
            conn = BaseHook.get_connection('azure_blob_default')
            conn_str = f"DefaultEndpointsProtocol=https;AccountName={conn.host};AccountKey={conn.password};EndpointSuffix=core.windows.net"
            
            client = BlobServiceClient.from_connection_string(conn_str)
            container_client = client.get_container_client(CONTAINER)
            
            # List blobs in source folder
            blobs = []
            for blob in container_client.list_blobs(name_starts_with=SOURCE_FOLDER):
                if blob.name != SOURCE_FOLDER + '/':  # Skip folder itself
                    blobs.append(blob.name)
            
            print(f"Found {len(blobs)} files in {SOURCE_FOLDER}")
            for blob in blobs:
                print(f"  - {blob}")
            
            context['task_instance'].xcom_push(key='source_files', value=blobs)
            return {
                'status': 'success',
                'file_count': len(blobs),
                'source_folder': SOURCE_FOLDER,
                'files': blobs
            }
        except Exception as e:
            print(f"Error listing files: {str(e)}")
            raise
    
    def move_files_to_target(**context):
        """Move files from source to target folder"""
        from azure.storage.blob import BlobServiceClient
        from airflow.hooks.base import BaseHook
        
        try:
            source_files = context['task_instance'].xcom_pull(
                task_ids='list_source',
                key='source_files'
            )
            
            if not source_files:
                print("No files to move")
                return {'status': 'no_files', 'moved_count': 0}
            
            # Get connection
            conn = BaseHook.get_connection('azure_blob_default')
            conn_str = f"DefaultEndpointsProtocol=https;AccountName={conn.host};AccountKey={conn.password};EndpointSuffix=core.windows.net"
            
            client = BlobServiceClient.from_connection_string(conn_str)
            container_client = client.get_container_client(CONTAINER)
            
            moved_count = 0
            moved_files = []
            
            for source_blob_path in source_files:
                try:
                    # Extract filename from source path
                    filename = source_blob_path.split('/')[-1]
                    target_blob_path = f"{TARGET_FOLDER}/{filename}"
                    
                    print(f"Moving: {source_blob_path} → {target_blob_path}")
                    
                    # Copy blob from source to target
                    source_blob_client = container_client.get_blob_client(source_blob_path)
                    source_blob_data = source_blob_client.download_blob().readall()
                    
                    target_blob_client = container_client.get_blob_client(target_blob_path)
                    target_blob_client.upload_blob(source_blob_data, overwrite=True)
                    
                    # Delete source blob
                    source_blob_client.delete_blob()
                    
                    moved_count += 1
                    moved_files.append(target_blob_path)
                    print(f"  ✓ Successfully moved: {filename}")
                    
                except Exception as e:
                    print(f"  ✗ Error moving {source_blob_path}: {str(e)}")
            
            context['task_instance'].xcom_push(key='moved_files', value=moved_files)
            
            return {
                'status': 'success',
                'moved_count': moved_count,
                'total_count': len(source_files),
                'moved_files': moved_files,
                'target_folder': TARGET_FOLDER
            }
        except Exception as e:
            print(f"Error moving files: {str(e)}")
            raise
    
    def verify_target_files(**context):
        """Verify files were successfully moved to target folder"""
        from azure.storage.blob import BlobServiceClient
        from airflow.hooks.base import BaseHook
        
        try:
            moved_files = context['task_instance'].xcom_pull(
                task_ids='move_files',
                key='moved_files'
            )
            
            # Get connection
            conn = BaseHook.get_connection('azure_blob_default')
            conn_str = f"DefaultEndpointsProtocol=https;AccountName={conn.host};AccountKey={conn.password};EndpointSuffix=core.windows.net"
            
            client = BlobServiceClient.from_connection_string(conn_str)
            container_client = client.get_container_client(CONTAINER)
            
            # List all files in target folder
            target_blobs = []
            for blob in container_client.list_blobs(name_starts_with=TARGET_FOLDER):
                if blob.name != TARGET_FOLDER + '/':  # Skip folder itself
                    target_blobs.append(blob.name)
            
            print(f"Verification: Found {len(target_blobs)} files in {TARGET_FOLDER}")
            for blob in target_blobs:
                print(f"  - {blob}")
            
            # Verify moved files are in target
            verified = 0
            for file_path in moved_files:
                if file_path in target_blobs:
                    verified += 1
            
            print(f"✓ Verified {verified}/{len(moved_files)} files successfully moved")
            
            return {
                'status': 'verified',
                'target_files_count': len(target_blobs),
                'verified_count': verified,
                'target_folder': TARGET_FOLDER
            }
        except Exception as e:
            print(f"Error verifying files: {str(e)}")
            raise
    
    # Tasks
    list_source = PythonOperator(
        task_id='list_source',
        python_callable=list_source_files,
        provide_context=True,
    )
    
    move_files = PythonOperator(
        task_id='move_files',
        python_callable=move_files_to_target,
        provide_context=True,
    )
    
    verify = PythonOperator(
        task_id='verify_target',
        python_callable=verify_target_files,
        provide_context=True,
    )
    
    # Pipeline
    list_source >> move_files >> verify
