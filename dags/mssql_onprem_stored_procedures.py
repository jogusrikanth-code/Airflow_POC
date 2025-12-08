"""
SQL Server Stored Procedure Execution
======================================
Execute SQL Server stored procedures from Airflow.
Demonstrates parameter passing and result handling.

What you need:
1. SQL Server connection 'mssql_onprem' configured
2. Stored procedures created in your database

Example stored procedures to create:
```sql
-- Simple procedure
CREATE PROCEDURE [dbo].[sp_get_order_summary]
    @start_date DATE,
    @end_date DATE
AS
BEGIN
    SELECT 
        COUNT(*) AS total_orders,
        SUM(order_amount) AS total_amount,
        AVG(order_amount) AS avg_amount
    FROM [dbo].[orders]
    WHERE order_date BETWEEN @start_date AND @end_date;
END

-- Data processing procedure
CREATE PROCEDURE [dbo].[sp_process_daily_orders]
    @batch_date DATE
AS
BEGIN
    -- Your ETL logic here
    INSERT INTO [dbo].[processed_orders]
    SELECT * FROM [dbo].[raw_orders]
    WHERE CAST(created_at AS DATE) = @batch_date;
    
    SELECT @@ROWCOUNT AS rows_processed;
END
```
"""
from airflow import DAG
from airflow.providers.microsoft.mssql.operators.mssql import MsSqlOperator
from airflow.providers.microsoft.mssql.hooks.mssql import MsSqlHook
from airflow.operators.python import PythonOperator
from datetime import datetime, timedelta

MSSQL_CONN_ID = 'mssql_onprem'

default_args = {
    'owner': 'airflow',
    'retries': 1,
    'retry_delay': timedelta(minutes=5),
}

with DAG(
    dag_id='mssql_onprem_stored_procedures',
    default_args=default_args,
    description='Execute SQL Server stored procedures',
    schedule=None,
    start_date=datetime(2025, 1, 1),
    catchup=False,
    tags=['mssql', 'onprem', 'stored-procedure'],
) as dag:
    
    # Method 1: Execute stored procedure with parameters using MsSqlOperator
    exec_summary_proc = MsSqlOperator(
        task_id='exec_order_summary',
        mssql_conn_id=MSSQL_CONN_ID,
        sql="""
        DECLARE @start_date DATE = CAST(DATEADD(day, -7, GETDATE()) AS DATE);
        DECLARE @end_date DATE = CAST(GETDATE() AS DATE);
        
        EXEC [dbo].[sp_get_order_summary]
            @start_date = @start_date,
            @end_date = @end_date;
        """,
    )
    
    # Method 2: Execute procedure with dynamic parameters using Python
    def exec_proc_with_params(**context):
        """Execute stored procedure with dynamic parameters"""
        hook = MsSqlHook(mssql_conn_id=MSSQL_CONN_ID)
        
        # Get batch date (today or from config)
        batch_date = datetime.now().strftime('%Y-%m-%d')
        
        print(f"Executing procedure for batch date: {batch_date}")
        
        # Execute stored procedure
        sql = f"""
        DECLARE @batch_date DATE = '{batch_date}';
        EXEC [dbo].[sp_process_daily_orders] @batch_date = @batch_date;
        """
        
        result = hook.get_first(sql)
        
        print(f"Procedure result: {result}")
        
        return {
            'batch_date': batch_date,
            'rows_processed': result[0] if result else 0,
            'status': 'completed'
        }
    
    exec_processing_proc = PythonOperator(
        task_id='exec_daily_processing',
        python_callable=exec_proc_with_params,
    )
    
    # Method 3: Execute multiple procedures in sequence
    exec_proc_chain = MsSqlOperator(
        task_id='exec_procedure_chain',
        mssql_conn_id=MSSQL_CONN_ID,
        sql="""
        -- Step 1: Cleanup old data
        EXEC [dbo].[sp_cleanup_old_data] @days_to_keep = 90;
        
        -- Step 2: Rebuild indexes
        EXEC [dbo].[sp_rebuild_indexes] @table_name = 'orders';
        
        -- Step 3: Update statistics
        EXEC [dbo].[sp_update_statistics] @table_name = 'orders';
        
        -- Return completion status
        SELECT 
            'Procedure chain completed' AS status,
            GETDATE() AS completed_at;
        """,
    )
    
    # Method 4: Execute procedure and check results
    def exec_and_validate(**context):
        """Execute procedure and validate results"""
        hook = MsSqlHook(mssql_conn_id=MSSQL_CONN_ID)
        
        # Execute procedure that returns data
        sql = """
        EXEC [dbo].[sp_get_order_summary]
            @start_date = CAST(DATEADD(day, -30, GETDATE()) AS DATE),
            @end_date = CAST(GETDATE() AS DATE);
        """
        
        records = hook.get_records(sql)
        
        if records:
            total_orders, total_amount, avg_amount = records[0]
            
            print(f"📊 Order Summary (Last 30 Days):")
            print(f"  Total Orders: {total_orders}")
            print(f"  Total Amount: ${total_amount:,.2f}")
            print(f"  Average Amount: ${avg_amount:,.2f}")
            
            # Validate results
            if total_orders == 0:
                print("⚠️  Warning: No orders found in the last 30 days")
            else:
                print("✅ Validation passed")
            
            return {
                'total_orders': total_orders,
                'total_amount': float(total_amount),
                'avg_amount': float(avg_amount)
            }
        else:
            raise ValueError("No results returned from stored procedure")
    
    exec_with_validation = PythonOperator(
        task_id='exec_with_validation',
        python_callable=exec_and_validate,
    )
    
    # Execute procedures in parallel or sequence
    # Parallel execution
    [exec_summary_proc, exec_processing_proc] >> exec_proc_chain >> exec_with_validation
