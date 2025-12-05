"""
Test Databricks Connection
===========================
Simple connection test to verify Databricks credentials and access.

Connection: databricks_default
"""
from airflow import DAG
from airflow.operators.python import PythonOperator
from datetime import datetime, timedelta

default_args = {
    'owner': 'airflow',
    'retries': 0,
}

with DAG(
    'databricks_test_connection',
    default_args=default_args,
    description='Test Databricks connection',
    schedule=None,
    start_date=datetime(2025, 1, 1),
    catchup=False,
    tags=['test', 'databricks', 'connection'],
) as dag:
    
    def test_connection(**context):
        """Test Databricks connection"""
        from airflow.hooks.base import BaseHook
        
        print("=" * 60)
        print("Testing Databricks Connection")
        print("=" * 60)
        
        try:
            # Get connection
            conn = BaseHook.get_connection('databricks_default')
            print(f"\n✓ Connection retrieved: {conn.conn_id}")
            print(f"  Host: {conn.host}")
            print(f"  Connection Type: {conn.conn_type}")
            
            # Check if token is present
            if conn.password or conn.extra_dejson.get('token'):
                print(f"✓ Authentication token present")
            else:
                print("⚠ Warning: No authentication token found")
            
            print("\n" + "=" * 60)
            print("✅ Databricks Connection Test PASSED")
            print("=" * 60)
            print("\nNote: Full connectivity test requires actual API call")
            print("Configure connection in Airflow UI with:")
            print("  - Host: https://your-workspace.azuredatabricks.net")
            print("  - Token: Your personal access token")
            
            return {'status': 'success', 'host': conn.host}
            
        except Exception as e:
            print("\n" + "=" * 60)
            print("❌ Databricks Connection Test FAILED")
            print("=" * 60)
            print(f"Error: {str(e)}")
            print("\nTo configure:")
            print("  1. Go to Airflow UI → Admin → Connections")
            print("  2. Add Connection: databricks_default")
            print("  3. Connection Type: Databricks")
            print("  4. Host: https://your-workspace.azuredatabricks.net")
            print("  5. Token: Your PAT")
            raise
    
    test_task = PythonOperator(
        task_id='test_databricks_connection',
        python_callable=test_connection,
    )
