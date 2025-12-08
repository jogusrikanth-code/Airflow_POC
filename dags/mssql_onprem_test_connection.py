"""
SQL Server Connection Test
===========================
Simple test to verify SQL Server connection.

What you need:
1. SQL Server connection 'mssql_onprem' configured in Airflow UI

Connection setup:
- Connection ID: mssql_onprem
- Type: Microsoft SQL Server
- Host: your-sql-server.domain.com
- Schema: YourDatabase
- Login: your_username
- Password: your_password
- Port: 1433
"""
from airflow import DAG
from airflow.providers.microsoft.mssql.operators.mssql import MsSqlOperator
from datetime import datetime

with DAG(
    'mssql_onprem_test_connection',
    description='Test SQL Server on-premise connection',
    schedule=None,
    start_date=datetime(2025, 1, 1),
    catchup=False,
    tags=['mssql', 'onprem', 'test'],
) as dag:
    
    # Test 1: Server version and basic info
    test_server_info = MsSqlOperator(
        task_id='test_server_info',
        mssql_conn_id='mssql_onprem',
        sql="""
        SELECT 
            @@VERSION AS sql_server_version,
            @@SERVERNAME AS server_name,
            DB_NAME() AS database_name,
            SUSER_NAME() AS login_user,
            GETDATE() AS current_time;
        """,
    )
    
    # Test 2: List databases
    list_databases = MsSqlOperator(
        task_id='list_databases',
        mssql_conn_id='mssql_onprem',
        sql="SELECT name AS database_name, create_date FROM sys.databases WHERE name NOT IN ('master', 'tempdb', 'model', 'msdb') ORDER BY name;",
    )
    
    # Test 3: List tables in current database
    list_tables = MsSqlOperator(
        task_id='list_tables',
        mssql_conn_id='mssql_onprem',
        sql="""
        SELECT 
            SCHEMA_NAME(schema_id) AS schema_name,
            name AS table_name,
            create_date
        FROM sys.tables
        ORDER BY schema_name, table_name;
        """,
    )
    
    # Test 4: Check permissions
    check_permissions = MsSqlOperator(
        task_id='check_permissions',
        mssql_conn_id='mssql_onprem',
        sql="""
        SELECT 
            permission_name,
            state_desc
        FROM sys.database_permissions
        WHERE grantee_principal_id = USER_ID();
        """,
    )
    
    test_server_info >> [list_databases, list_tables, check_permissions]
