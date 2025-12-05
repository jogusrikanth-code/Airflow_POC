"""
Test Azure Blob Storage Connection
===================================
Simple connection test to verify Azure credentials and access.

Connection: azure_blob_default
"""
from airflow import DAG
from airflow.operators.python import PythonOperator
from datetime import datetime, timedelta

default_args = {
    'owner': 'airflow',
    'retries': 0,
}

with DAG(
    'test_azure_connection',
    default_args=default_args,
    description='Test Azure Blob Storage connection',
    schedule=None,
    start_date=datetime(2025, 1, 1),
    catchup=False,
    tags=['test', 'azure', 'connection'],
) as dag:
    
    def test_connection(**context):
        """Test Azure Blob Storage connection"""
        from azure.storage.blob import BlobServiceClient
        from airflow.hooks.base import BaseHook
        
        print("=" * 60)
        print("Testing Azure Blob Storage Connection")
        print("=" * 60)
        
        # Get connection
        conn = BaseHook.get_connection('azure_blob_default')
        print(f"\n✓ Connection retrieved: {conn.conn_id}")
        print(f"  Storage Account: {conn.host}")
        
        # Build connection string
        conn_str = f"DefaultEndpointsProtocol=https;AccountName={conn.host};AccountKey={conn.password};EndpointSuffix=core.windows.net"
        
        # Test connection
        client = BlobServiceClient.from_connection_string(conn_str)
        print(f"✓ BlobServiceClient created successfully")
        
        # List containers
        containers = list(client.list_containers())
        print(f"\n✓ Found {len(containers)} containers:")
        for container in containers[:5]:
            print(f"  - {container.name}")
        
        print("\n" + "=" * 60)
        print("✅ Azure Blob Storage Connection Test PASSED")
        print("=" * 60)
        
        return {'status': 'success', 'storage_account': conn.host, 'containers': len(containers)}
    
    test_task = PythonOperator(
        task_id='test_azure_connection',
        python_callable=test_connection,
    )
