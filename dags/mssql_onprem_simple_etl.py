"""
SQL Server On-Premise Simple ETL
==================================
Simple ETL workflow for on-premise SQL Server:
- Extract: Query source table
- Transform: Execute stored procedure
- Load: Insert into target table
- Validate: Check data quality

What you need:
1. SQL Server connection 'mssql_onprem' configured in Airflow
2. Tables: [dbo].[source_orders], [dbo].[target_orders]
3. Optional: Stored procedure [dbo].[sp_transform_orders]

Connection setup in Airflow UI:
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
from airflow.providers.microsoft.mssql.hooks.mssql import MsSqlHook
from airflow.operators.python import PythonOperator
from datetime import datetime, timedelta

# Configuration
MSSQL_CONN_ID = 'mssql_onprem'
SOURCE_TABLE = '[dbo].[source_orders]'
TARGET_TABLE = '[dbo].[target_orders]'
STAGING_TABLE = '[dbo].[staging_orders]'

default_args = {
    'owner': 'airflow',
    'retries': 2,
    'retry_delay': timedelta(minutes=5),
}

with DAG(
    dag_id='mssql_onprem_simple_etl',
    default_args=default_args,
    description='Simple ETL from SQL Server source to target table',
    schedule=None,  # Manual trigger
    start_date=datetime(2025, 1, 1),
    catchup=False,
    tags=['mssql', 'onprem', 'etl', 'simple'],
) as dag:
    
    # Task 1: Test connection
    test_connection = MsSqlOperator(
        task_id='test_connection',
        mssql_conn_id=MSSQL_CONN_ID,
        sql="SELECT @@VERSION AS version, DB_NAME() AS database_name, GETDATE() AS current_time;",
    )
    
    # Task 2: Create staging table if not exists
    create_staging = MsSqlOperator(
        task_id='create_staging_table',
        mssql_conn_id=MSSQL_CONN_ID,
        sql=f"""
        IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = 'staging_orders')
        BEGIN
            CREATE TABLE {STAGING_TABLE} (
                order_id INT,
                customer_id INT,
                order_amount DECIMAL(10,2),
                order_date DATE,
                extracted_at DATETIME DEFAULT GETDATE()
            );
        END
        """,
    )
    
    # Task 3: Extract - Copy recent orders to staging
    extract_data = MsSqlOperator(
        task_id='extract_to_staging',
        mssql_conn_id=MSSQL_CONN_ID,
        sql=f"""
        -- Clear staging table
        TRUNCATE TABLE {STAGING_TABLE};
        
        -- Extract last 7 days of orders
        INSERT INTO {STAGING_TABLE} (order_id, customer_id, order_amount, order_date)
        SELECT 
            order_id,
            customer_id,
            order_amount,
            order_date
        FROM {SOURCE_TABLE}
        WHERE order_date >= CAST(DATEADD(day, -7, GETDATE()) AS DATE);
        
        -- Return count
        SELECT COUNT(*) AS rows_extracted FROM {STAGING_TABLE};
        """,
    )
    
    # Task 4: Transform - Apply business logic (server-side)
    transform_data = MsSqlOperator(
        task_id='transform_data',
        mssql_conn_id=MSSQL_CONN_ID,
        sql=f"""
        -- Add calculated columns in staging
        ALTER TABLE {STAGING_TABLE} ADD 
            tax_amount AS (order_amount * 0.08),
            total_amount AS (order_amount * 1.08);
        
        -- Or execute stored procedure
        -- EXEC [dbo].[sp_transform_orders] @batch_date = CAST(GETDATE() AS DATE);
        
        SELECT COUNT(*) AS rows_transformed FROM {STAGING_TABLE};
        """,
    )
    
    # Task 5: Load - Insert into target table
    load_data = MsSqlOperator(
        task_id='load_to_target',
        mssql_conn_id=MSSQL_CONN_ID,
        sql=f"""
        -- Create target table if not exists
        IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = 'target_orders')
        BEGIN
            CREATE TABLE {TARGET_TABLE} (
                order_id INT PRIMARY KEY,
                customer_id INT,
                order_amount DECIMAL(10,2),
                tax_amount DECIMAL(10,2),
                total_amount DECIMAL(10,2),
                order_date DATE,
                loaded_at DATETIME DEFAULT GETDATE()
            );
        END
        
        -- Merge staging into target (UPSERT)
        MERGE {TARGET_TABLE} AS target
        USING {STAGING_TABLE} AS source
        ON target.order_id = source.order_id
        WHEN MATCHED THEN
            UPDATE SET 
                customer_id = source.customer_id,
                order_amount = source.order_amount,
                order_date = source.order_date,
                loaded_at = GETDATE()
        WHEN NOT MATCHED THEN
            INSERT (order_id, customer_id, order_amount, order_date)
            VALUES (source.order_id, source.customer_id, source.order_amount, source.order_date);
        
        SELECT COUNT(*) AS rows_loaded FROM {TARGET_TABLE};
        """,
    )
    
    # Task 6: Validate data quality
    def validate_quality(**context):
        """Validate loaded data using Python"""
        hook = MsSqlHook(mssql_conn_id=MSSQL_CONN_ID)
        
        # Row count check
        staging_count = hook.get_first(f"SELECT COUNT(*) FROM {STAGING_TABLE}")[0]
        target_count = hook.get_first(f"SELECT COUNT(*) FROM {TARGET_TABLE} WHERE CAST(loaded_at AS DATE) = CAST(GETDATE() AS DATE)")[0]
        
        print(f"Staging rows: {staging_count}")
        print(f"Target rows (today): {target_count}")
        
        # Null value check
        null_check = hook.get_first(f"SELECT COUNT(*) FROM {TARGET_TABLE} WHERE order_amount IS NULL OR customer_id IS NULL")[0]
        
        print(f"Null values found: {null_check}")
        
        if null_check > 0:
            raise ValueError(f"Data quality issue: {null_check} rows have null values in critical columns")
        
        print("✅ Data quality validation passed")
        
        return {
            'staging_rows': staging_count,
            'target_rows': target_count,
            'null_values': null_check,
            'status': 'PASSED'
        }
    
    validate = PythonOperator(
        task_id='validate_quality',
        python_callable=validate_quality,
    )
    
    # Task 7: Cleanup staging
    cleanup = MsSqlOperator(
        task_id='cleanup_staging',
        mssql_conn_id=MSSQL_CONN_ID,
        sql=f"TRUNCATE TABLE {STAGING_TABLE};",
    )
    
    # Pipeline flow
    test_connection >> create_staging >> extract_data >> transform_data >> load_data >> validate >> cleanup
