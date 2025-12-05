"""
Databricks Job Trigger via Direct API
======================================
Triggers Databricks jobs using direct REST API calls.
This approach uses Python requests library instead of SDK.

Connection: databricks_default
"""
from airflow import DAG
from airflow.operators.python import PythonOperator
from datetime import datetime, timedelta
import requests
import json

default_args = {
    'owner': 'airflow',
    'retries': 2,
    'retry_delay': timedelta(minutes=5),
}

with DAG(
    'databricks_trigger_via_api',
    default_args=default_args,
    description='Trigger Databricks jobs using REST API directly',
    schedule=None,  # Manual trigger only
    start_date=datetime(2025, 1, 1),
    catchup=False,
    tags=['databricks', 'api', 'trigger'],
) as dag:
    
    def trigger_job_via_api(**context):
        """
        Trigger a Databricks job using REST API
        This bypasses the SDK and uses direct HTTP calls
        """
        from airflow.hooks.base import BaseHook
        
        # Get connection details
        conn = BaseHook.get_connection('databricks_default')
        host = conn.host.rstrip('/')
        token = conn.password
        
        # Job ID to trigger (replace with your actual job ID)
        job_id = 123  # CHANGE THIS to your job ID
        
        print("=" * 70)
        print("TRIGGERING DATABRICKS JOB VIA REST API")
        print("=" * 70)
        print(f"\nWorkspace: {host}")
        print(f"Job ID: {job_id}")
        
        # API endpoint
        url = f"{host}/api/2.1/jobs/run-now"
        
        # Headers
        headers = {
            'Authorization': f'Bearer {token}',
            'Content-Type': 'application/json'
        }
        
        # Payload
        payload = {
            'job_id': job_id,
            'notebook_params': {
                'execution_date': context['ds'],
                'dag_run_id': context['run_id']
            }
        }
        
        print(f"\n🔄 Sending POST request to: {url}")
        print(f"Payload: {json.dumps(payload, indent=2)}")
        
        try:
            # Make the API call
            response = requests.post(
                url,
                headers=headers,
                json=payload,
                timeout=30
            )
            
            # Check response
            if response.status_code == 200:
                result = response.json()
                run_id = result.get('run_id')
                print(f"\n✅ SUCCESS! Job triggered")
                print(f"Run ID: {run_id}")
                print(f"Response: {json.dumps(result, indent=2)}")
                
                return {
                    'status': 'success',
                    'job_id': job_id,
                    'run_id': run_id,
                    'workspace': host
                }
            else:
                print(f"\n❌ Failed to trigger job")
                print(f"Status Code: {response.status_code}")
                print(f"Response: {response.text}")
                
                return {
                    'status': 'failed',
                    'error_code': response.status_code,
                    'error_message': response.text
                }
                
        except requests.exceptions.RequestException as e:
            print(f"\n❌ Request Error: {str(e)}")
            return {
                'status': 'error',
                'error': str(e)
            }
    
    def check_job_status(**context):
        """
        Check the status of a triggered job
        """
        from airflow.hooks.base import BaseHook
        import time
        
        # Get the run_id from previous task
        ti = context['ti']
        result = ti.xcom_pull(task_ids='trigger_job')
        
        if not result or result.get('status') != 'success':
            print("⚠️  No run_id found, skipping status check")
            return
        
        run_id = result.get('run_id')
        conn = BaseHook.get_connection('databricks_default')
        host = conn.host.rstrip('/')
        token = conn.password
        
        print(f"\n🔍 Checking status for Run ID: {run_id}")
        
        # API endpoint
        url = f"{host}/api/2.1/jobs/runs/get"
        headers = {
            'Authorization': f'Bearer {token}',
            'Content-Type': 'application/json'
        }
        
        params = {'run_id': run_id}
        
        try:
            response = requests.get(url, headers=headers, params=params, timeout=30)
            
            if response.status_code == 200:
                run_info = response.json()
                state = run_info.get('state', {})
                life_cycle_state = state.get('life_cycle_state')
                result_state = state.get('result_state')
                
                print(f"\n📊 Job Status:")
                print(f"  Life Cycle State: {life_cycle_state}")
                print(f"  Result State: {result_state}")
                
                return {
                    'run_id': run_id,
                    'life_cycle_state': life_cycle_state,
                    'result_state': result_state
                }
            else:
                print(f"❌ Failed to get status: {response.text}")
                
        except Exception as e:
            print(f"❌ Error checking status: {str(e)}")
    
    # Tasks
    trigger_job = PythonOperator(
        task_id='trigger_job',
        python_callable=trigger_job_via_api,
    )
    
    check_status = PythonOperator(
        task_id='check_status',
        python_callable=check_job_status,
    )
    
    # Task dependencies
    trigger_job >> check_status
