"""
PowerBI Dataset Refresh Pipeline
=================================
Orchestrates data refresh for PowerBI datasets after ETL completion.

Features:
- Uses built-in operators for file operations
- Checks data freshness before triggering refresh
- Monitors refresh completion
- Sends notifications on success/failure

Schedule: Triggered after ETL pipeline completes
Dependencies: end_to_end_etl_pipeline
"""

from airflow import DAG
from airflow.operators.python import PythonOperator, BranchPythonOperator
from airflow.operators.empty import EmptyOperator
from airflow.sensors.external_task import ExternalTaskSensor
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)


# --------------------------------------------------------------------------------
# TASK FUNCTIONS
# --------------------------------------------------------------------------------

def check_data_freshness(**context):
    """Check if data lake has fresh data before refreshing PowerBI."""
    from airflow.providers.microsoft.azure.hooks.wasb import WasbHook
    from datetime import datetime, timedelta
    
    execution_date = context['ds']
    logger.info(f"Checking data freshness for {execution_date}")
    
    # Get Azure Blob Hook
    hook = WasbHook(wasb_conn_id='azure_blob_default')
    client = hook.get_conn()
    
    # Check gold layer for recent data
    container = client.get_container_client("sg-analytics-gold")
    gold_path = f"gold/daily_sales_summary/{execution_date}.csv"
    
    try:
        blob = container.get_blob_client(gold_path)
        properties = blob.get_blob_properties()
        
        # Check if file was modified recently (within last hour)
        last_modified = properties.last_modified
        now = datetime.now(last_modified.tzinfo)
        age_minutes = (now - last_modified).total_seconds() / 60
        
        logger.info(f"File last modified: {last_modified} ({age_minutes:.1f} minutes ago)")
        
        if age_minutes > 120:  # More than 2 hours old
            logger.warning(f"Data is stale ({age_minutes:.1f} minutes old)")
            return 'data_stale'
        
        logger.info("✓ Data is fresh, proceeding with refresh")
        return 'data_fresh'
        
    except Exception as e:
        logger.error(f"Failed to check data freshness: {str(e)}")
        return 'check_failed'


def trigger_powerbi_refresh(**context):
    """Trigger PowerBI dataset refresh using REST API."""
    import requests
    from airflow.models import Variable
    
    logger.info("Triggering PowerBI dataset refresh...")
    
    # Get PowerBI credentials from Airflow Variables
    tenant_id = Variable.get("powerbi_tenant_id")
    client_id = Variable.get("powerbi_client_id")
    client_secret = Variable.get("powerbi_client_secret")
    
    # Get access token
    token_url = f"https://login.microsoftonline.com/{tenant_id}/oauth2/v2.0/token"
    token_data = {
        'grant_type': 'client_credentials',
        'client_id': client_id,
        'client_secret': client_secret,
        'scope': 'https://analysis.windows.net/powerbi/api/.default'
    }
    
    token_response = requests.post(token_url, data=token_data)
    token_response.raise_for_status()
    access_token = token_response.json()['access_token']
    
    # Trigger dataset refresh
    workspace_id = Variable.get("powerbi_workspace_id")
    dataset_id = Variable.get("powerbi_dataset_id")
    
    refresh_url = f"https://api.powerbi.com/v1.0/myorg/groups/{workspace_id}/datasets/{dataset_id}/refreshes"
    
    headers = {
        'Authorization': f'Bearer {access_token}',
        'Content-Type': 'application/json'
    }
    
    refresh_response = requests.post(refresh_url, headers=headers)
    refresh_response.raise_for_status()
    
    logger.info("✓ PowerBI dataset refresh triggered successfully")
    
    return {
        'workspace_id': workspace_id,
        'dataset_id': dataset_id,
        'refresh_triggered_at': datetime.now().isoformat()
    }


def monitor_powerbi_refresh(**context):
    """Monitor PowerBI refresh status and wait for completion."""
    import requests
    import time
    from airflow.models import Variable
    
    logger.info("Monitoring PowerBI refresh status...")
    
    # Get PowerBI credentials
    tenant_id = Variable.get("powerbi_tenant_id")
    client_id = Variable.get("powerbi_client_id")
    client_secret = Variable.get("powerbi_client_secret")
    workspace_id = Variable.get("powerbi_workspace_id")
    dataset_id = Variable.get("powerbi_dataset_id")
    
    # Get access token
    token_url = f"https://login.microsoftonline.com/{tenant_id}/oauth2/v2.0/token"
    token_data = {
        'grant_type': 'client_credentials',
        'client_id': client_id,
        'client_secret': client_secret,
        'scope': 'https://analysis.windows.net/powerbi/api/.default'
    }
    
    token_response = requests.post(token_url, data=token_data)
    token_response.raise_for_status()
    access_token = token_response.json()['access_token']
    
    headers = {'Authorization': f'Bearer {access_token}'}
    
    # Poll refresh status
    status_url = f"https://api.powerbi.com/v1.0/myorg/groups/{workspace_id}/datasets/{dataset_id}/refreshes"
    
    max_wait_minutes = 30
    check_interval_seconds = 30
    start_time = datetime.now()
    
    while True:
        elapsed = (datetime.now() - start_time).total_seconds() / 60
        
        if elapsed > max_wait_minutes:
            raise TimeoutError(f"PowerBI refresh timeout after {max_wait_minutes} minutes")
        
        # Get latest refresh status
        status_response = requests.get(status_url, headers=headers, params={'$top': 1})
        status_response.raise_for_status()
        
        refreshes = status_response.json().get('value', [])
        if not refreshes:
            raise ValueError("No refresh history found")
        
        latest_refresh = refreshes[0]
        status = latest_refresh.get('status')
        
        logger.info(f"  Refresh status: {status} (elapsed: {elapsed:.1f} minutes)")
        
        if status == 'Completed':
            logger.info("✓ PowerBI refresh completed successfully")
            return {
                'status': 'completed',
                'duration_minutes': elapsed,
                'end_time': latest_refresh.get('endTime')
            }
        
        elif status == 'Failed':
            error_msg = latest_refresh.get('serviceExceptionJson', 'Unknown error')
            raise ValueError(f"PowerBI refresh failed: {error_msg}")
        
        elif status in ['InProgress', 'Unknown']:
            time.sleep(check_interval_seconds)
        
        else:
            raise ValueError(f"Unexpected refresh status: {status}")


def send_refresh_notification(**context):
    """Send notification about PowerBI refresh completion."""
    execution_date = context['ds']
    monitor_result = context['ti'].xcom_pull(task_ids='monitor_refresh')
    
    duration = monitor_result.get('duration_minutes', 0)
    
    logger.info(f"PowerBI refresh completed for {execution_date}")
    logger.info(f"Refresh duration: {duration:.1f} minutes")
    
    # In production: send email/Slack notification
    # For now, just log
    
    return {
        'notification_sent': True,
        'execution_date': execution_date,
        'duration_minutes': duration
    }


def handle_stale_data(**context):
    """Handle case when data is too old."""
    logger.warning("Data is stale - skipping PowerBI refresh")
    logger.info("Please check upstream ETL pipeline")
    
    # In production: send alert to data team
    
    return {'action': 'skipped', 'reason': 'stale_data'}


def handle_check_failed(**context):
    """Handle case when data freshness check failed."""
    logger.error("Data freshness check failed")
    
    # In production: send alert
    
    raise ValueError("Unable to verify data freshness")


# --------------------------------------------------------------------------------
# DAG DEFINITION
# --------------------------------------------------------------------------------

default_args = {
    'owner': 'business_intelligence',
    'depends_on_past': False,
    'email': ['bi-team@spencergifts.com'],
    'email_on_failure': True,
    'retries': 2,
    'retry_delay': timedelta(minutes=5),
    'execution_timeout': timedelta(hours=1),
}

with DAG(
    dag_id='powerbi_refresh_pipeline',
    default_args=default_args,
    description='Refresh PowerBI datasets after ETL completion',
    schedule=None,  # Triggered by external events
    start_date=datetime(2025, 12, 1),
    catchup=False,
    max_active_runs=1,
    tags=['powerbi', 'bi', 'refresh'],
    doc_md=__doc__
) as dag:
    
    # Wait for upstream ETL pipeline to complete
    wait_for_etl = ExternalTaskSensor(
        task_id='wait_for_etl_completion',
        external_dag_id='end_to_end_etl_pipeline',
        external_task_id='end',
        allowed_states=['success'],
        failed_states=['failed', 'skipped'],
        mode='reschedule',
        timeout=7200,  # 2 hours
        poke_interval=300  # Check every 5 minutes
    )
    
    # Check data freshness
    check_freshness = BranchPythonOperator(
        task_id='check_data_freshness',
        python_callable=check_data_freshness
    )
    
    # Data is fresh - proceed with refresh
    data_fresh = EmptyOperator(task_id='data_fresh')
    
    trigger_refresh = PythonOperator(
        task_id='trigger_refresh',
        python_callable=trigger_powerbi_refresh
    )
    
    monitor_refresh = PythonOperator(
        task_id='monitor_refresh',
        python_callable=monitor_powerbi_refresh
    )
    
    send_notification = PythonOperator(
        task_id='send_notification',
        python_callable=send_refresh_notification
    )
    
    # Data is stale - skip refresh
    data_stale = PythonOperator(
        task_id='data_stale',
        python_callable=handle_stale_data
    )
    
    # Check failed
    check_failed = PythonOperator(
        task_id='check_failed',
        python_callable=handle_check_failed
    )
    
    # End marker
    end = EmptyOperator(
        task_id='end',
        trigger_rule='none_failed_min_one_success'
    )
    
    # Pipeline flow
    wait_for_etl >> check_freshness
    check_freshness >> [data_fresh, data_stale, check_failed]
    data_fresh >> trigger_refresh >> monitor_refresh >> send_notification >> end
    data_stale >> end
    check_failed >> end
