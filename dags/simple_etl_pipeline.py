"""
Simple End-to-End ETL Pipeline DAG
===================================
Basic linear ETL pipeline demonstrating:
- Copy files from landing zone to bronze layer (server-side)
- Validate files exist and are non-empty
- Copy validated files to silver layer (server-side)
- Send completion notification

All file operations use Azure server-side copy - no data flows through Airflow!

Schedule: Daily at 2 AM
"""

from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.operators.empty import EmptyOperator
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)


# --------------------------------------------------------------------------------
# TASK FUNCTIONS
# --------------------------------------------------------------------------------

def copy_to_bronze(**context):
    """Copy files from landing zone to bronze layer (server-side copy)."""
    from airflow.providers.microsoft.azure.hooks.wasb import WasbHook
    
    execution_date = context['ds']
    hook = WasbHook(wasb_conn_id='azure_blob_default')
    client = hook.get_conn()
    
    source_container = "sg-analytics-raw"
    target_container = "sg-analytics-bronze"
    source_prefix = f"landing_zone/{execution_date}/"
    
    logger.info(f"Copying {source_container}/{source_prefix} → {target_container}/bronze/")
    
    source = client.get_container_client(source_container)
    target = client.get_container_client(target_container)
    
    files_copied = 0
    for blob in source.list_blobs(name_starts_with=source_prefix):
        target_name = f"bronze/{execution_date}/{blob.name.split('/')[-1]}"
        source_url = f"{client.account_url}/{source_container}/{blob.name}"
        target_blob = target.get_blob_client(target_name)
        target_blob.start_copy_from_url(source_url)
        files_copied += 1
        logger.info(f"  ✓ {blob.name}")
    
    logger.info(f"Copied {files_copied} files (server-side)")
    return {'files_copied': files_copied}


def validate_bronze(**context):
    """Validate files exist and are non-empty in bronze layer."""
    from airflow.providers.microsoft.azure.hooks.wasb import WasbHook
    
    execution_date = context['ds']
    hook = WasbHook(wasb_conn_id='azure_blob_default')
    client = hook.get_conn()
    
    container = client.get_container_client("sg-analytics-bronze")
    prefix = f"bronze/{execution_date}/"
    
    logger.info(f"Validating files in {prefix}")
    
    files_validated = 0
    for blob in container.list_blobs(name_starts_with=prefix):
        if blob.size == 0:
            raise ValueError(f"Empty file found: {blob.name}")
        logger.info(f"  ✓ {blob.name} ({blob.size:,} bytes)")
        files_validated += 1
    
    if files_validated == 0:
        raise ValueError("No files found to validate")
    
    logger.info(f"Validated {files_validated} files")
    return {'files_validated': files_validated}


def copy_to_silver(**context):
    """Copy validated files from bronze to silver layer (server-side copy)."""
    from airflow.providers.microsoft.azure.hooks.wasb import WasbHook
    
    execution_date = context['ds']
    hook = WasbHook(wasb_conn_id='azure_blob_default')
    client = hook.get_conn()
    
    source_container = "sg-analytics-bronze"
    target_container = "sg-analytics-silver"
    source_prefix = f"bronze/{execution_date}/"
    
    logger.info(f"Copying {source_container}/{source_prefix} → {target_container}/silver/")
    
    source = client.get_container_client(source_container)
    target = client.get_container_client(target_container)
    
    files_copied = 0
    for blob in source.list_blobs(name_starts_with=source_prefix):
        target_name = blob.name.replace("bronze/", "silver/")
        source_url = f"{client.account_url}/{source_container}/{blob.name}"
        target_blob = target.get_blob_client(target_name)
        target_blob.start_copy_from_url(source_url)
        files_copied += 1
        logger.info(f"  ✓ {blob.name}")
    
    logger.info(f"Copied {files_copied} files to silver layer (server-side)")
    return {'files_copied': files_copied}


def send_notification(**context):
    """Log pipeline completion."""
    execution_date = context['ds']
    logger.info(f"✓ Pipeline completed successfully for {execution_date}")
    return {'status': 'success'}


# --------------------------------------------------------------------------------
# DAG DEFINITION
# --------------------------------------------------------------------------------

default_args = {
    'owner': 'data_engineering',
    'retries': 2,
    'retry_delay': timedelta(minutes=5),
}

with DAG(
    dag_id='simple_etl_pipeline',
    default_args=default_args,
    description='📦 Simple Linear ETL | Landing → Bronze → Silver',
    schedule='0 2 * * *',  # Daily at 2 AM
    start_date=datetime(2025, 12, 1),
    catchup=False,
    tags=['📦 etl', '🟢 simple', '☁️ azure', '⚡ fast', '✅ production'],
    doc_md=__doc__,
    params={
        'source_container': 'sg-analytics-raw',
        'bronze_container': 'sg-analytics-bronze',
        'silver_container': 'sg-analytics-silver'
    }
) as dag:
    
    start = EmptyOperator(task_id='start', doc_md="### 🚀 Pipeline Start\nInitialize ETL pipeline execution")
    
    copy_bronze = PythonOperator(
        task_id='copy_to_bronze',
        python_callable=copy_to_bronze,
        doc_md="### 🔵 Bronze Layer Ingestion\n**Action**: Server-side copy from landing zone\n**Performance**: ~100x faster than download/upload"
    )
    
    validate = PythonOperator(
        task_id='validate_bronze',
        python_callable=validate_bronze,
        doc_md="### 🔍 Data Quality Validation\n**Checks**: File existence, non-zero size\n**Fail Fast**: Stops pipeline on critical issues"
    )
    
    copy_silver = PythonOperator(
        task_id='copy_to_silver',
        python_callable=copy_to_silver,
        doc_md="### 🟡 Silver Layer Promotion\n**Action**: Promote validated files to silver layer\n**Method**: Azure server-side copy"
    )
    
    notify = PythonOperator(
        task_id='notify',
        python_callable=send_notification,
        doc_md="### 🔔 Success Notification\n**Action**: Log completion metrics\n**Status**: Pipeline completed successfully ✓"
    )
    
    end = EmptyOperator(task_id='end', doc_md="### ✅ Pipeline Complete\nAll stages executed successfully")
    
    # Simple linear flow: start → bronze → validate → silver → notify → end
    start >> copy_bronze >> validate >> copy_silver >> notify >> end
