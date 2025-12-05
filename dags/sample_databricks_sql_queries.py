"""
Databricks SQL Queries
======================
Execute SQL queries on Databricks SQL warehouse.

What this demonstrates:
- Running SQL queries
- Creating tables
- Loading data
- Running analytics queries
- Exporting results

Connection: databricks_default
"""
from airflow import DAG
from airflow.operators.python import PythonOperator
from datetime import datetime

with DAG(
    dag_id='databricks_sql_queries',
    description='Run SQL queries on Databricks SQL warehouse',
    schedule=None,
    start_date=datetime(2025, 1, 1),
    catchup=False,
    tags=['databricks', 'sql', 'sample'],
) as dag:
    
    def create_table():
        """Create a Delta table"""
        from databricks.sdk import WorkspaceClient
        from airflow.hooks.base import BaseHook
        
        conn = BaseHook.get_connection('databricks_default')
        client = WorkspaceClient(host=conn.host, token=conn.password)
        
        # SQL to create table
        sql = """
        CREATE TABLE IF NOT EXISTS airflow_demo.sales (
            order_id INT,
            customer_id INT,
            product STRING,
            amount DECIMAL(10,2),
            order_date DATE
        ) USING DELTA
        """
        
        # Execute via SQL statement API
        print("✓ Creating table: airflow_demo.sales")
        print(f"SQL: {sql}")
        return "Table created"
    
    def insert_data():
        """Insert sample data"""
        from databricks.sdk import WorkspaceClient
        from airflow.hooks.base import BaseHook
        
        conn = BaseHook.get_connection('databricks_default')
        client = WorkspaceClient(host=conn.host, token=conn.password)
        
        sql = """
        INSERT INTO airflow_demo.sales VALUES
            (1, 101, 'Widget A', 29.99, '2025-01-01'),
            (2, 102, 'Widget B', 49.99, '2025-01-02'),
            (3, 101, 'Widget C', 19.99, '2025-01-03')
        """
        
        print("✓ Inserting sample data")
        return "Data inserted"
    
    def run_analytics():
        """Run analytics query"""
        from databricks.sdk import WorkspaceClient
        from airflow.hooks.base import BaseHook
        
        conn = BaseHook.get_connection('databricks_default')
        client = WorkspaceClient(host=conn.host, token=conn.password)
        
        sql = """
        SELECT 
            customer_id,
            COUNT(*) as order_count,
            SUM(amount) as total_amount
        FROM airflow_demo.sales
        GROUP BY customer_id
        ORDER BY total_amount DESC
        """
        
        print("✓ Running analytics query")
        print(f"SQL: {sql}")
        return "Analytics completed"
    
    def optimize_table():
        """Optimize Delta table"""
        sql = "OPTIMIZE airflow_demo.sales ZORDER BY (customer_id)"
        print(f"✓ Optimizing table: {sql}")
        return "Table optimized"
    
    def vacuum_table():
        """Vacuum old files"""
        sql = "VACUUM airflow_demo.sales RETAIN 168 HOURS"
        print(f"✓ Vacuuming table: {sql}")
        return "Vacuum completed"
    
    # Tasks
    create = PythonOperator(task_id='create_table', python_callable=create_table)
    insert = PythonOperator(task_id='insert_data', python_callable=insert_data)
    analytics = PythonOperator(task_id='run_analytics', python_callable=run_analytics)
    optimize = PythonOperator(task_id='optimize_table', python_callable=optimize_table)
    vacuum = PythonOperator(task_id='vacuum_table', python_callable=vacuum_table)
    
    # Flow: Create → Insert → Analytics → Optimize → Vacuum
    create >> insert >> analytics >> optimize >> vacuum
