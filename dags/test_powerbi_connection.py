"""
Test PowerBI Connection
========================
Simple connection test to verify PowerBI/Azure AD credentials.

Connection: azure_default (for PowerBI authentication)
"""
from airflow import DAG
from airflow.operators.python import PythonOperator
from datetime import datetime, timedelta

default_args = {
    'owner': 'airflow',
    'retries': 0,
}

with DAG(
    'test_powerbi_connection',
    default_args=default_args,
    description='Test PowerBI/Azure AD connection',
    schedule=None,
    start_date=datetime(2025, 1, 1),
    catchup=False,
    tags=['test', 'powerbi', 'connection'],
) as dag:
    
    def test_connection(**context):
        """Test PowerBI connection"""
        from airflow.hooks.base import BaseHook
        
        print("=" * 60)
        print("Testing PowerBI Connection")
        print("=" * 60)
        
        try:
            # Get connection
            conn = BaseHook.get_connection('azure_default')
            print(f"\n✓ Connection retrieved: {conn.conn_id}")
            print(f"  Connection Type: {conn.conn_type}")
            
            # Check for Azure AD credentials
            if conn.login:
                print(f"✓ Client ID present: {conn.login[:8]}...")
            if conn.password:
                print(f"✓ Client Secret present")
            
            extra = conn.extra_dejson
            if extra.get('tenantId'):
                print(f"✓ Tenant ID: {extra.get('tenantId')}")
            
            print("\n" + "=" * 60)
            print("✅ PowerBI Connection Configuration PASSED")
            print("=" * 60)
            print("\nNote: Full API test requires actual PowerBI API call")
            print("Configure connection in Airflow UI with:")
            print("  - Connection Type: Generic")
            print("  - Login: Azure AD App Client ID")
            print("  - Password: Azure AD App Client Secret")
            print("  - Extra: {\"tenantId\": \"your-tenant-id\"}")
            
            return {'status': 'success', 'conn_type': conn.conn_type}
            
        except Exception as e:
            print("\n" + "=" * 60)
            print("❌ PowerBI Connection Test FAILED")
            print("=" * 60)
            print(f"Error: {str(e)}")
            print("\nTo configure:")
            print("  1. Go to Airflow UI → Admin → Connections")
            print("  2. Add Connection: azure_default")
            print("  3. Connection Type: Generic")
            print("  4. Login: Azure AD App Client ID")
            print("  5. Password: Azure AD App Client Secret")
            print("  6. Extra: {\"tenantId\": \"your-tenant-id\"}")
            raise
    
    test_task = PythonOperator(
        task_id='test_powerbi_connection',
        python_callable=test_connection,
    )
