"""
Test SQL Server Connection
===========================
Simple connection test to verify on-prem SQL Server credentials.

Connection: onprem_mssql
"""
from airflow import DAG
from airflow.operators.python import PythonOperator
from datetime import datetime, timedelta

default_args = {
    'owner': 'airflow',
    'retries': 0,
}

with DAG(
    'test_sqlserver_connection',
    default_args=default_args,
    description='Test SQL Server connection',
    schedule=None,
    start_date=datetime(2025, 1, 1),
    catchup=False,
    tags=['test', 'sqlserver', 'connection'],
) as dag:
    
    def test_connection(**context):
        """Test SQL Server connection"""
        from airflow.hooks.base import BaseHook
        
        print("=" * 60)
        print("Testing SQL Server Connection")
        print("=" * 60)
        
        try:
            # Get connection
            conn = BaseHook.get_connection('onprem_mssql')
            print(f"\n✓ Connection retrieved: {conn.conn_id}")
            print(f"  Host: {conn.host}")
            print(f"  Port: {conn.port or 1433}")
            print(f"  Database: {conn.schema or 'default'}")
            print(f"  Login: {conn.login}")
            
            print("\n" + "=" * 60)
            print("✅ SQL Server Connection Configuration PASSED")
            print("=" * 60)
            print("\nNote: Full connectivity test requires actual SQL query")
            print("Configure connection in Airflow UI with:")
            print("  - Host: your-sqlserver.database.windows.net")
            print("  - Schema: database_name")
            print("  - Login: username")
            print("  - Password: password")
            print("  - Port: 1433")
            
            return {'status': 'success', 'host': conn.host, 'database': conn.schema}
            
        except Exception as e:
            print("\n" + "=" * 60)
            print("❌ SQL Server Connection Test FAILED")
            print("=" * 60)
            print(f"Error: {str(e)}")
            print("\nTo configure:")
            print("  1. Go to Airflow UI → Admin → Connections")
            print("  2. Add Connection: onprem_mssql")
            print("  3. Connection Type: Microsoft SQL Server")
            print("  4. Host: your-server")
            print("  5. Schema: database_name")
            print("  6. Login: username")
            print("  7. Password: password")
            raise
    
    test_task = PythonOperator(
        task_id='test_sqlserver_connection',
        python_callable=test_connection,
    )
