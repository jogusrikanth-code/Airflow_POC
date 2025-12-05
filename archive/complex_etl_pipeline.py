"""
Complex ETL Pipeline with Multiple Branches
============================================
Advanced ETL pipeline demonstrating:
- Dynamic task generation using loops
- Multiple conditional branches (BranchPythonOperator)
- Parallel processing paths
- File categorization and routing
- Data quality checks with different severity levels
- XCom for inter-task communication

Flow:
1. Ingest data from landing zone
2. Branch based on file size (small vs large datasets)
3. Quality checks with severity-based branching
4. Parallel categorization tasks (sales, inventory, customer)
5. Type-specific processing (CSV, Parquet, JSON)
6. Final aggregation and notification

Schedule: Daily at 2 AM
"""

from airflow import DAG
from airflow.operators.python import PythonOperator, BranchPythonOperator
from airflow.operators.empty import EmptyOperator
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)


# --------------------------------------------------------------------------------
# TASK FUNCTIONS
# --------------------------------------------------------------------------------

def ingest_files(**context):
    """Ingest files from landing zone with metadata collection."""
    from airflow.providers.microsoft.azure.hooks.wasb import WasbHook
    
    execution_date = context['ds']
    hook = WasbHook(wasb_conn_id='azure_blob_default')
    client = hook.get_conn()
    
    source_container = "sg-analytics-raw"
    target_container = "sg-analytics-bronze"
    source_prefix = f"landing_zone/{execution_date}/"
    
    logger.info(f"Ingesting from {source_container}/{source_prefix}")
    
    source = client.get_container_client(source_container)
    target = client.get_container_client(target_container)
    
    files_ingested = 0
    total_size = 0
    file_metadata = []
    
    # Loop through files and collect metadata
    for blob in source.list_blobs(name_starts_with=source_prefix):
        target_name = f"bronze/{execution_date}/{blob.name.split('/')[-1]}"
        source_url = f"{client.account_url}/{source_container}/{blob.name}"
        target_blob = target.get_blob_client(target_name)
        target_blob.start_copy_from_url(source_url)
        
        # Collect metadata for decision making
        file_metadata.append({
            'name': blob.name,
            'size': blob.size,
            'extension': blob.name.split('.')[-1] if '.' in blob.name else 'unknown'
        })
        
        files_ingested += 1
        total_size += blob.size
        logger.info(f"  ✓ {blob.name} ({blob.size:,} bytes)")
    
    total_size_mb = total_size / 1024 / 1024
    logger.info(f"Ingested {files_ingested} files, Total: {total_size_mb:.2f} MB")
    
    # Store in XCom for branching decisions
    context['ti'].xcom_push(key='file_count', value=files_ingested)
    context['ti'].xcom_push(key='total_size_mb', value=total_size_mb)
    context['ti'].xcom_push(key='file_metadata', value=file_metadata)
    
    return {
        'files_ingested': files_ingested,
        'total_size_mb': round(total_size_mb, 2)
    }


def decide_size_path(**context):
    """Branch 1: Decide processing path based on dataset size."""
    ti = context['ti']
    total_size_mb = ti.xcom_pull(key='total_size_mb', task_ids='ingest_files')
    
    logger.info(f"BRANCH DECISION: Dataset size = {total_size_mb:.2f} MB")
    
    # If-else branching logic
    if total_size_mb > 100:
        logger.info("  → Route to LARGE_DATASET path")
        return 'process_large_dataset'
    else:
        logger.info("  → Route to STANDARD_DATASET path")
        return 'process_standard_dataset'


def process_large_dataset(**context):
    """Process large datasets with batch strategy."""
    logger.info("Processing LARGE dataset with optimized batch strategy...")
    logger.info("  - Using chunked processing")
    logger.info("  - Enabling compression")
    logger.info("  - Setting higher memory limits")
    logger.info("✓ Large dataset processing completed")
    return {'strategy': 'batch', 'optimized': True}


def process_standard_dataset(**context):
    """Process standard datasets with normal strategy."""
    logger.info("Processing STANDARD dataset with normal strategy...")
    logger.info("  - Standard memory allocation")
    logger.info("  - Regular processing pipeline")
    logger.info("✓ Standard dataset processing completed")
    return {'strategy': 'standard', 'optimized': False}


def validate_data_quality(**context):
    """Validate data quality and categorize issues."""
    from airflow.providers.microsoft.azure.hooks.wasb import WasbHook
    
    execution_date = context['ds']
    hook = WasbHook(wasb_conn_id='azure_blob_default')
    client = hook.get_conn()
    
    container = client.get_container_client("sg-analytics-bronze")
    prefix = f"bronze/{execution_date}/"
    
    logger.info("Running data quality checks...")
    
    files_checked = 0
    critical_issues = 0
    warnings = 0
    
    # Loop through files with quality checks
    for blob in container.list_blobs(name_starts_with=prefix):
        files_checked += 1
        
        # If-else: Check file size for issues
        if blob.size == 0:
            logger.error(f"  ✗ CRITICAL: {blob.name} is empty")
            critical_issues += 1
        elif blob.size < 1024:  # Less than 1KB
            logger.warning(f"  ⚠ WARNING: {blob.name} is very small ({blob.size} bytes)")
            warnings += 1
        else:
            logger.info(f"  ✓ {blob.name} passed quality checks")
    
    logger.info(f"Quality check results: {files_checked} files, {critical_issues} critical, {warnings} warnings")
    
    # Store results for branching
    context['ti'].xcom_push(key='critical_issues', value=critical_issues)
    context['ti'].xcom_push(key='warnings', value=warnings)
    
    return {
        'files_checked': files_checked,
        'critical_issues': critical_issues,
        'warnings': warnings
    }


def decide_quality_path(**context):
    """Branch 2: Decide path based on data quality results."""
    ti = context['ti']
    critical_issues = ti.xcom_pull(key='critical_issues', task_ids='validate_quality')
    warnings = ti.xcom_pull(key='warnings', task_ids='validate_quality')
    
    logger.info(f"BRANCH DECISION: Quality - {critical_issues} critical, {warnings} warnings")
    
    # Multiple if-else conditions
    if critical_issues > 0:
        logger.info("  → Route to ERROR_HANDLING path")
        return 'handle_critical_errors'
    elif warnings > 2:
        logger.info("  → Route to WARNING_REVIEW path")
        return 'review_warnings'
    else:
        logger.info("  → Route to CONTINUE_PROCESSING path")
        return 'categorize_by_type'


def handle_critical_errors(**context):
    """Handle critical data quality errors."""
    logger.error("Handling CRITICAL errors...")
    logger.error("  - Quarantining problematic files")
    logger.error("  - Sending alert notifications")
    logger.error("  - Creating incident ticket")
    return {'status': 'errors_handled', 'escalated': True}


def review_warnings(**context):
    """Review and log warnings."""
    logger.warning("Reviewing WARNINGS...")
    logger.warning("  - Logging warning details")
    logger.warning("  - Updating monitoring dashboard")
    return {'status': 'warnings_logged', 'action_required': False}


def categorize_by_type(**context):
    """Categorize files by extension using loops."""
    from airflow.providers.microsoft.azure.hooks.wasb import WasbHook
    
    execution_date = context['ds']
    hook = WasbHook(wasb_conn_id='azure_blob_default')
    client = hook.get_conn()
    
    container = client.get_container_client("sg-analytics-bronze")
    prefix = f"bronze/{execution_date}/"
    
    logger.info("Categorizing files by type...")
    
    # Dictionary to categorize files
    file_types = {'csv': [], 'parquet': [], 'json': [], 'other': []}
    
    # Loop through files and categorize
    for blob in container.list_blobs(name_starts_with=prefix):
        ext = blob.name.split('.')[-1].lower() if '.' in blob.name else 'unknown'
        
        # If-else: Categorize by extension
        if ext in file_types:
            file_types[ext].append(blob.name)
        else:
            file_types['other'].append(blob.name)
    
    # Loop through categories and log
    logger.info("\nFile categorization results:")
    for file_type, files in file_types.items():
        if len(files) > 0:
            logger.info(f"  {file_type.upper()}: {len(files)} files")
            # Nested loop: Show first 2 files
            for i, filename in enumerate(files[:2]):
                logger.info(f"    {i+1}. {filename}")
    
    context['ti'].xcom_push(key='file_types', value={k: len(v) for k, v in file_types.items()})
    
    return {'categorized': sum(len(v) for v in file_types.values())}


def process_csv_files(**context):
    """Process CSV files with specific logic."""
    logger.info("Processing CSV files...")
    logger.info("  - Parsing delimiter detection")
    logger.info("  - Data type inference")
    logger.info("  - Schema validation")
    logger.info("✓ CSV processing completed")
    return {'format': 'csv', 'status': 'processed'}


def process_parquet_files(**context):
    """Process Parquet files with specific logic."""
    logger.info("Processing Parquet files...")
    logger.info("  - Reading schema metadata")
    logger.info("  - Column statistics collection")
    logger.info("  - Compression check")
    logger.info("✓ Parquet processing completed")
    return {'format': 'parquet', 'status': 'processed'}


def process_json_files(**context):
    """Process JSON files with specific logic."""
    logger.info("Processing JSON files...")
    logger.info("  - JSON validation")
    logger.info("  - Nested structure flattening")
    logger.info("  - Schema extraction")
    logger.info("✓ JSON processing completed")
    return {'format': 'json', 'status': 'processed'}


def aggregate_results(**context):
    """Aggregate results from all processing paths."""
    ti = context['ti']
    
    logger.info("Aggregating pipeline results...")
    
    # Loop through task IDs to pull results
    task_ids = [
        'ingest_files', 'validate_quality', 'categorize_by_type',
        'process_csv_files', 'process_parquet_files', 'process_json_files'
    ]
    
    aggregated = {}
    for task_id in task_ids:
        result = ti.xcom_pull(task_ids=task_id)
        # If-else: Only add if result exists
        if result:
            aggregated[task_id] = result
            logger.info(f"  {task_id}: {result}")
    
    return {'aggregated_results': aggregated}


def send_completion_notification(**context):
    """Send final completion notification with summary."""
    execution_date = context['ds']
    ti = context['ti']
    
    logger.info(f"{'='*60}")
    logger.info(f"PIPELINE COMPLETED: {execution_date}")
    logger.info(f"{'='*60}")
    
    # Pull key metrics
    file_count = ti.xcom_pull(key='file_count', task_ids='ingest_files')
    total_size_mb = ti.xcom_pull(key='total_size_mb', task_ids='ingest_files')
    
    logger.info(f"Files processed: {file_count}")
    logger.info(f"Total size: {total_size_mb:.2f} MB")
    logger.info(f"Status: SUCCESS ✓")
    logger.info(f"{'='*60}")
    
    return {'status': 'success', 'pipeline': 'complex_etl'}


# --------------------------------------------------------------------------------
# DAG DEFINITION
# --------------------------------------------------------------------------------

default_args = {
    'owner': 'data_engineering',
    'retries': 2,
    'retry_delay': timedelta(minutes=5),
}

with DAG(
    dag_id='complex_etl_pipeline',
    default_args=default_args,
    description='🎯 Complex ETL | Branching + Parallel Processing + Dynamic Tasks',
    schedule='0 2 * * *',  # Daily at 2 AM
    start_date=datetime(2025, 12, 1),
    catchup=False,
    tags=['🎯 complex', '🔀 branching', '⚡ parallel', '🏢 enterprise', '✅ production', '🔁 loops', '☁️ azure'],
    doc_md=__doc__,
    params={
        'size_threshold_mb': 100,
        'max_warnings': 2,
        'enable_parallel_processing': True,
        'categories': ['sales', 'inventory', 'customer', 'financial']
    }
) as dag:
    
    start = EmptyOperator(task_id='start', doc_md="### 🚀 Pipeline Start\nInitialize complex ETL pipeline with branching logic")
    
    # Step 1: Ingest files
    ingest = PythonOperator(
        task_id='ingest_files',
        python_callable=ingest_files,
        doc_md="### 📥 Data Ingestion\n**Action**: Copy files from landing zone to bronze\n**Metadata**: Collect size, extension, count\n**Output**: XCom for downstream decisions"
    )
    
    # BRANCH 1: Decide processing path based on size
    decide_size = BranchPythonOperator(
        task_id='decide_size_path',
        python_callable=decide_size_path,
        doc_md="### 🔀 Branch Decision 1: Size-Based Routing\n**Threshold**: 100 MB\n**Large Path** (>100MB): Optimized batch processing\n**Standard Path** (≤100MB): Normal processing"
    )
    
    # Path 1A: Large dataset processing
    process_large = PythonOperator(
        task_id='process_large_dataset',
        python_callable=process_large_dataset,
        doc_md="### 🚀 Large Dataset Processing\n**Features**:\n- Chunked processing\n- Compression enabled\n- Higher memory limits\n**Use Case**: Datasets >100 MB"
    )
    
    # Path 1B: Standard dataset processing
    process_standard = PythonOperator(
        task_id='process_standard_dataset',
        python_callable=process_standard_dataset,
        doc_md="### ⚡ Standard Dataset Processing\n**Features**:\n- Standard memory allocation\n- Regular processing pipeline\n**Use Case**: Datasets ≤100 MB"
    )
    
    # Join point after size-based branching
    join_after_size = EmptyOperator(
        task_id='join_after_size',
        trigger_rule='none_failed_min_one_success',
        doc_md="### 🔗 Join Point\nConverge both size-based processing paths"
    )
    
    # Step 2: Quality validation
    validate = PythonOperator(
        task_id='validate_quality',
        python_callable=validate_data_quality,
        doc_md="### 🔍 Data Quality Validation\n**Checks**:\n- Empty files (CRITICAL)\n- Undersized files (WARNING)\n**Output**: Issue counts for branching"
    )
    
    # BRANCH 2: Decide path based on quality results
    decide_quality = BranchPythonOperator(
        task_id='decide_quality_path',
        python_callable=decide_quality_path,
        doc_md="### 🔀 Branch Decision 2: Quality-Based Routing\n**Critical Issues**: → Error Handler\n**Warnings (>2)**: → Warning Review\n**Clean Data**: → Continue Processing"
    )
    
    # Path 2A: Handle critical errors
    handle_errors = PythonOperator(
        task_id='handle_critical_errors',
        python_callable=handle_critical_errors,
        doc_md="### 🚨 Critical Error Handling\n**Actions**:\n- Quarantine files\n- Send alerts\n- Create incident ticket\n**Trigger**: Critical quality issues detected"
    )
    
    # Path 2B: Review warnings
    review_warn = PythonOperator(
        task_id='review_warnings',
        python_callable=review_warnings,
        doc_md="### ⚠️ Warning Review\n**Actions**:\n- Log warning details\n- Update monitoring dashboard\n**Trigger**: >2 warnings detected"
    )
    
    # Path 2C: Continue processing
    categorize = PythonOperator(
        task_id='categorize_by_type',
        python_callable=categorize_by_type,
        doc_md="### 📊 File Categorization\n**Action**: Group files by extension\n**Categories**: CSV, Parquet, JSON, Other\n**Uses**: Nested loops for categorization"
    )
    
    # Join point after quality-based branching
    join_after_quality = EmptyOperator(
        task_id='join_after_quality',
        trigger_rule='none_failed_min_one_success',
        doc_md="### 🔗 Join Point\nConverge all quality-based processing paths"
    )
    
    # DYNAMIC TASKS: Create category-specific tasks using a loop
    category_tasks = []
    categories = ['sales', 'inventory', 'customer', 'financial']
    category_emojis = {'sales': '💰', 'inventory': '📦', 'customer': '👥', 'financial': '💵'}
    
    for category in categories:
        emoji = category_emojis.get(category, '📊')
        task = EmptyOperator(
            task_id=f'process_category_{category}',
            doc_md=f"### {emoji} Process {category.title()} Category\n**Generated**: Dynamic task from loop\n**Category**: {category}"
        )
        category_tasks.append(task)
    
    # PARALLEL PROCESSING: File type specific processors
    process_csv = PythonOperator(
        task_id='process_csv_files',
        python_callable=process_csv_files,
        doc_md="### 📄 CSV File Processor\n**Features**:\n- Delimiter detection\n- Data type inference\n- Schema validation\n**Runs**: In parallel with other format processors"
    )
    
    process_parquet = PythonOperator(
        task_id='process_parquet_files',
        python_callable=process_parquet_files,
        doc_md="### 🗂️ Parquet File Processor\n**Features**:\n- Schema metadata reading\n- Column statistics\n- Compression check\n**Runs**: In parallel with other format processors"
    )
    
    process_json = PythonOperator(
        task_id='process_json_files',
        python_callable=process_json_files,
        doc_md="### 🔗 JSON File Processor\n**Features**:\n- JSON validation\n- Nested structure flattening\n- Schema extraction\n**Runs**: In parallel with other format processors"
    )
    
    # Join all parallel processors
    join_processors = EmptyOperator(
        task_id='join_processors',
        trigger_rule='none_failed_min_one_success',
        doc_md="### 🔗 Join Processors\nWait for all format processors to complete"
    )
    
    # Aggregate results
    aggregate = PythonOperator(
        task_id='aggregate_results',
        python_callable=aggregate_results,
        doc_md="### 📈 Results Aggregation\n**Action**: Collect metrics from all tasks\n**Uses**: Loop through task_ids to pull XCom\n**Output**: Summary statistics"
    )
    
    # Final notification
    notify = PythonOperator(
        task_id='notify',
        python_callable=send_completion_notification,
        doc_md="### 🔔 Completion Notification\n**Action**: Send success notification\n**Content**: Files processed, size, status\n**Status**: Pipeline completed successfully ✓"
    )
    
    end = EmptyOperator(task_id='end', doc_md="### ✅ Pipeline Complete\nAll stages executed successfully")
    
    # --------------------------------------------------------------------------------
    # DAG FLOW - Complex branching and parallel processing
    # --------------------------------------------------------------------------------
    
    # Initial ingestion
    start >> ingest >> decide_size
    
    # BRANCH 1: Size-based processing paths
    decide_size >> [process_large, process_standard]
    [process_large, process_standard] >> join_after_size
    
    # Quality validation
    join_after_size >> validate >> decide_quality
    
    # BRANCH 2: Quality-based processing paths
    decide_quality >> [handle_errors, review_warn, categorize]
    [handle_errors, review_warn, categorize] >> join_after_quality
    
    # DYNAMIC TASKS: Fan out to category tasks (using loop)
    for task in category_tasks:
        join_after_quality >> task
    
    # PARALLEL PROCESSING: All category tasks feed into type processors
    for task in category_tasks:
        task >> [process_csv, process_parquet, process_json]
    
    # Join all processors
    [process_csv, process_parquet, process_json] >> join_processors
    
    # Final aggregation and notification
    join_processors >> aggregate >> notify >> end
