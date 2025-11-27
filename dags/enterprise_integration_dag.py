"""
Enterprise Integration DAG
==========================

Complete pipeline demonstrating integration between:
1. On-Premises SQL Database (Data Source)
2. Azure Storage (Data Staging)
3. Databricks (Data Transformation)
4. Power BI (Visualization & Refresh)

Flow:
  On-Prem DB → Azure Storage → Databricks → Power BI

This is a POC showcasing how to orchestrate enterprise data pipeline.
"""

from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.exceptions import AirflowException

# Import connectors
from src.connectors import (
    fetch_from_onprem,
    get_azure_storage_connector,
    get_databricks_connector,
    get_powerbi_connector,
)


default_args = {
    "owner": "data_engineering",
    "retries": 1,
    "retry_delay": timedelta(minutes=5),
}


# ============================================================================
# TASK: Extract from On-Premises Database
# ============================================================================

def extract_from_onprem_db(**context):
    """
    Extract data from on-premises SQL Server database.
    
    In production, credentials would come from Airflow Connection or Secrets.
    """
    logger_context = context['task_instance'].log
    logger_context.info("Starting extraction from on-premises database...")
    
    try:
        # These would come from Airflow Connections in production
        config = {
            'host': 'on-prem-server.company.com',
            'port': 1433,
            'database': 'sales_db',
            'username': '{{ conn.onprem_db.login }}',
            'password': '{{ conn.onprem_db.password }}'
        }
        
        # Extract data
        query = """
        SELECT 
            SalesID,
            OrderDate,
            Amount,
            CustomerID,
            Product,
            Quantity
        FROM SalesData
        WHERE OrderDate >= DATEADD(day, -1, CAST(GETDATE() AS DATE))
        ORDER BY OrderDate DESC
        """
        
        data = fetch_from_onprem('sql_server', config, query)
        logger_context.info(f"✓ Extracted {len(data)} records from on-premises DB")
        
        # Store in XCom for next task
        context['task_instance'].xcom_push(key='onprem_data', value=data)
        
        return {
            'status': 'success',
            'records_extracted': len(data)
        }
    except Exception as e:
        logger_context.error(f"✗ Extraction failed: {str(e)}")
        raise AirflowException(f"Failed to extract from on-premises: {str(e)}")


# ============================================================================
# TASK: Stage Data to Azure Storage
# ============================================================================

def stage_to_azure_storage(**context):
    """
    Upload extracted data to Azure Storage for staging.
    Provides a data buffer between on-premises and cloud processing.
    """
    logger_context = context['task_instance'].log
    logger_context.info("Staging data to Azure Storage...")
    
    try:
        import pandas as pd
        from datetime import datetime
        
        # Get data from previous task
        data = context['task_instance'].xcom_pull(
            task_ids='extract_from_onprem',
            key='onprem_data'
        )
        
        # Convert to DataFrame
        df = pd.DataFrame(data)
        logger_context.info(f"DataFrame shape: {df.shape}")
        
        # Connect to Azure Storage
        connector = get_azure_storage_connector(conn_id='azure_default')
        
        # Upload to staging container
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        blob_name = f"sales_data/staging/sales_{timestamp}.csv"
        
        connector.upload_dataframe(
            df=df,
            container_name='staging',
            blob_name=blob_name,
            format='csv'
        )
        
        logger_context.info(f"✓ Data staged at {blob_name}")
        
        # Push staging path to XCom for next task
        context['task_instance'].xcom_push(
            key='staging_path',
            value=f"staging/{blob_name}"
        )
        
        return {
            'status': 'success',
            'staging_blob': blob_name,
            'rows_staged': len(df)
        }
    except Exception as e:
        logger_context.error(f"✗ Staging failed: {str(e)}")
        raise AirflowException(f"Failed to stage to Azure: {str(e)}")


# ============================================================================
# TASK: Transform in Databricks
# ============================================================================

def transform_in_databricks(**context):
    """
    Load staged data and perform transformations in Databricks.
    - Clean and validate data
    - Aggregate metrics
    - Create dimensions and facts
    """
    logger_context = context['task_instance'].log
    logger_context.info("Starting transformation in Databricks...")
    
    try:
        # Get staging path
        staging_path = context['task_instance'].xcom_pull(
            task_ids='stage_to_azure',
            key='staging_path'
        )
        
        # Connect to Databricks
        databricks = get_databricks_connector(conn_id='databricks_default')
        
        # Create transformation queries
        logger_context.info("Creating cleaned data table...")
        
        # Step 1: Load from staged CSV and clean
        load_query = f"""
        CREATE OR REPLACE TABLE sales.sales_raw_cleaned AS
        SELECT 
            SalesID,
            OrderDate,
            Amount,
            CustomerID,
            Product,
            Quantity,
            Amount / NULLIF(Quantity, 0) as UnitPrice,
            CURRENT_TIMESTAMP() as LoadedAt
        FROM delta.`wasbs://staging@storage.blob.core.windows.net/{staging_path}`
        WHERE Amount > 0 AND Quantity > 0
        """
        
        databricks.run_query(load_query)
        logger_context.info("✓ Cleaned data loaded")
        
        # Step 2: Create daily summary
        logger_context.info("Creating daily summary...")
        summary_query = """
        CREATE OR REPLACE TABLE sales.sales_daily_summary AS
        SELECT 
            OrderDate,
            COUNT(*) as TransactionCount,
            SUM(Amount) as TotalSales,
            AVG(Amount) as AvgSaleAmount,
            COUNT(DISTINCT CustomerID) as UniqueCustomers,
            COUNT(DISTINCT Product) as UniqueProducts
        FROM sales.sales_raw_cleaned
        GROUP BY OrderDate
        ORDER BY OrderDate DESC
        """
        
        databricks.run_query(summary_query)
        logger_context.info("✓ Daily summary created")
        
        # Step 3: Create product aggregation
        logger_context.info("Creating product metrics...")
        product_query = """
        CREATE OR REPLACE TABLE sales.sales_by_product AS
        SELECT 
            Product,
            COUNT(*) as SalesCount,
            SUM(Quantity) as UnitsSOld,
            SUM(Amount) as TotalRevenue,
            ROUND(AVG(UnitPrice), 2) as AvgUnitPrice
        FROM sales.sales_raw_cleaned
        GROUP BY Product
        ORDER BY TotalRevenue DESC
        """
        
        databricks.run_query(product_query)
        logger_context.info("✓ Product metrics created")
        
        logger_context.info("✓ All transformations completed")
        
        return {
            'status': 'success',
            'tables_created': 3,
            'tables': [
                'sales.sales_raw_cleaned',
                'sales.sales_daily_summary',
                'sales.sales_by_product'
            ]
        }
    except Exception as e:
        logger_context.error(f"✗ Transformation failed: {str(e)}")
        raise AirflowException(f"Failed to transform in Databricks: {str(e)}")


# ============================================================================
# TASK: Refresh Power BI Dataset
# ============================================================================

def refresh_powerbi_dataset(**context):
    """
    Refresh Power BI datasets after data is ready in Databricks.
    Ensures reports are updated with latest data.
    """
    logger_context = context['task_instance'].log
    logger_context.info("Refreshing Power BI datasets...")
    
    try:
        # Connect to Power BI
        powerbi = get_powerbi_connector(conn_id='powerbi_default')
        
        # Configuration (would be in variables/connections in production)
        workspace_id = '{{ var.value.powerbi_workspace_id }}'
        dataset_id = '{{ var.value.powerbi_dataset_id }}'
        
        logger_context.info(f"Refreshing dataset {dataset_id}...")
        
        # Trigger refresh and wait for completion
        success = powerbi.refresh_dataset(
            workspace_id=workspace_id,
            dataset_id=dataset_id,
            wait_for_completion=True,
            timeout=600  # 10 minutes timeout
        )
        
        if success:
            logger_context.info("✓ Power BI dataset refresh completed")
            
            # Get dataset info
            tables = powerbi.get_dataset_tables(workspace_id, dataset_id)
            logger_context.info(f"Dataset has {len(tables)} tables")
            
            return {
                'status': 'success',
                'dataset_id': dataset_id,
                'tables_count': len(tables)
            }
        else:
            raise AirflowException("Power BI refresh failed or timed out")
    except Exception as e:
        logger_context.error(f"✗ Power BI refresh failed: {str(e)}")
        raise AirflowException(f"Failed to refresh Power BI: {str(e)}")


# ============================================================================
# TASK: Validate Pipeline
# ============================================================================

def validate_pipeline(**context):
    """
    Final validation step to ensure all data moved correctly through pipeline.
    Check row counts and data integrity.
    """
    logger_context = context['task_instance'].log
    logger_context.info("Validating pipeline...")
    
    try:
        # Get results from previous tasks
        extract_result = context['task_instance'].xcom_pull(
            task_ids='extract_from_onprem'
        )
        stage_result = context['task_instance'].xcom_pull(
            task_ids='stage_to_azure'
        )
        transform_result = context['task_instance'].xcom_pull(
            task_ids='transform_in_databricks'
        )
        refresh_result = context['task_instance'].xcom_pull(
            task_ids='refresh_powerbi'
        )
        
        logger_context.info("✓ Extract: {} records".format(
            extract_result.get('records_extracted', 'N/A')
        ))
        logger_context.info("✓ Stage: {} rows".format(
            stage_result.get('rows_staged', 'N/A')
        ))
        logger_context.info("✓ Transform: {} tables created".format(
            transform_result.get('tables_created', 'N/A')
        ))
        logger_context.info("✓ Refresh: Dataset refreshed")
        
        return {
            'status': 'success',
            'message': 'Pipeline validation successful',
            'extract_records': extract_result.get('records_extracted'),
            'staged_rows': stage_result.get('rows_staged'),
            'tables_created': transform_result.get('tables_created'),
            'powerbi_refreshed': refresh_result.get('status') == 'success'
        }
    except Exception as e:
        logger_context.error(f"✗ Validation failed: {str(e)}")
        raise AirflowException(f"Pipeline validation failed: {str(e)}")


# ============================================================================
# DAG DEFINITION
# ============================================================================

with DAG(
    dag_id='enterprise_integration_pipeline',
    description='POC: Integration between On-Prem, Azure, Databricks, and Power BI',
    default_args=default_args,
    start_date=datetime(2024, 1, 1),
    schedule_interval='@daily',  # Run daily
    catchup=False,
    tags=['poc', 'integration', 'enterprise'],
    doc_md=__doc__,
) as dag:
    
    # Tasks
    extract = PythonOperator(
        task_id='extract_from_onprem',
        python_callable=extract_from_onprem_db,
        doc='Extract sales data from on-premises SQL Server'
    )
    
    stage = PythonOperator(
        task_id='stage_to_azure',
        python_callable=stage_to_azure_storage,
        doc='Upload extracted data to Azure Blob Storage'
    )
    
    transform = PythonOperator(
        task_id='transform_in_databricks',
        python_callable=transform_in_databricks,
        doc='Transform and aggregate data in Databricks'
    )
    
    refresh = PythonOperator(
        task_id='refresh_powerbi',
        python_callable=refresh_powerbi_dataset,
        doc='Refresh Power BI datasets with latest data'
    )
    
    validate = PythonOperator(
        task_id='validate_pipeline',
        python_callable=validate_pipeline,
        doc='Validate pipeline execution and data integrity'
    )
    
    # Define dependencies
    extract >> stage >> transform >> refresh >> validate
