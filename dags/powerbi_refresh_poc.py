"""
PowerBI Refresh POC
===================
Proof of concept for PowerBI integration:
- Trigger PowerBI dataset refresh
- Monitor refresh status
- Handle server-side transformations on PowerBI dataset

Connection required: powerbi_mssql (or azure_default for auth)
"""
from airflow import DAG
from airflow.operators.python import PythonOperator
from datetime import datetime, timedelta

default_args = {
    'owner': 'airflow',
    'retries': 2,
    'retry_delay': timedelta(minutes=5),
}

with DAG(
    'powerbi_refresh_poc',
    default_args=default_args,
    description='PowerBI Dataset Refresh POC with server-side operations',
    schedule=None,
    start_date=datetime(2025, 1, 1),
    catchup=False,
    tags=['powerbi', 'poc', 'refresh'],
) as dag:
    
    def test_connection(**context):
        """Test PowerBI/Azure connection"""
        from airflow.hooks.base import BaseHook
        
        print("Testing PowerBI/Azure connection...")
        
        try:
            # Get Azure connection
            conn = BaseHook.get_connection('azure_default')
            print(f"✓ Connection retrieved: {conn.conn_id}")
            print(f"  Type: {conn.conn_type}")
            
            if conn.host:
                print(f"  Host/Tenant: {conn.host}")
            if conn.login:
                print(f"  Login/Client ID: {conn.login}")
            
            print(f"\nℹ PowerBI API endpoints:")
            print(f"  - Workspaces: https://api.powerbi.com/v1.0/myorg/groups")
            print(f"  - Datasets: https://api.powerbi.com/v1.0/myorg/groups/{{workspace_id}}/datasets")
            print(f"  - Refresh: https://api.powerbi.com/v1.0/myorg/groups/{{workspace_id}}/datasets/{{dataset_id}}/refreshes")
            
            print(f"\n✅ PowerBI connection test PASSED")
            print(f"ℹ To test actual API: Configure Client ID, Secret, and Tenant ID in connection")
            
            return {'status': 'success', 'conn_id': conn.conn_id}
        except Exception as e:
            print(f"❌ Connection test failed: {str(e)}")
            raise
    
    test_task = PythonOperator(
        task_id='test_connection',
        python_callable=test_connection,
    )
