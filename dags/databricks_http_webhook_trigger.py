"""
Databricks Job Trigger via Webhook
===================================
Alternative method: Use Databricks webhook to trigger jobs.
This can work even with network restrictions if webhook URL is accessible.

Connection: databricks_default
"""
from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.providers.http.operators.http import HttpOperator  # Updated for Airflow 3.0
from datetime import datetime, timedelta

default_args = {
    'owner': 'airflow',
    'retries': 1,
    'retry_delay': timedelta(minutes=2),
}

with DAG(
    'databricks_http_webhook_trigger',
    default_args=default_args,
    description='Trigger Databricks via webhook (alternative to SDK)',
    schedule=None,
    start_date=datetime(2025, 1, 1),
    catchup=False,
    tags=['databricks', 'webhook', 'alternative'],
) as dag:
    
    def trigger_via_curl(**context):
        """
        Use curl command to trigger job (bypasses Python SDK issues)
        """
        from airflow.hooks.base import BaseHook
        import subprocess
        
        conn = BaseHook.get_connection('databricks_default')
        host = conn.host.rstrip('/')
        token = conn.password
        job_id = 123  # CHANGE THIS
        
        print("=" * 70)
        print("TRIGGERING VIA CURL COMMAND")
        print("=" * 70)
        
        # Build curl command
        curl_cmd = [
            'curl', '-X', 'POST',
            f'{host}/api/2.1/jobs/run-now',
            '-H', f'Authorization: Bearer {token}',
            '-H', 'Content-Type: application/json',
            '-d', f'{{"job_id": {job_id}}}'
        ]
        
        try:
            print(f"\n🔄 Executing curl command...")
            result = subprocess.run(
                curl_cmd,
                capture_output=True,
                text=True,
                timeout=30
            )
            
            print(f"\nStatus Code: {result.returncode}")
            print(f"Output: {result.stdout}")
            
            if result.returncode == 0:
                print("\n✅ Job triggered successfully via curl")
                return {'status': 'success', 'output': result.stdout}
            else:
                print(f"\n❌ Error: {result.stderr}")
                return {'status': 'failed', 'error': result.stderr}
                
        except Exception as e:
            print(f"\n❌ Exception: {str(e)}")
            return {'status': 'error', 'error': str(e)}
    
    # Alternative: Use Airflow's HTTP operator (Airflow 3.0 syntax)
    trigger_http = HttpOperator(
        task_id='trigger_via_http',
        http_conn_id='databricks_default',
        endpoint='/api/2.1/jobs/run-now',
        method='POST',
        data='{"job_id": 123}',  # CHANGE job_id
        headers={
            'Content-Type': 'application/json'
        },
        response_check=lambda response: response.status_code == 200,
        log_response=True,
    )
    
    trigger_curl = PythonOperator(
        task_id='trigger_via_curl',
        python_callable=trigger_via_curl,
    )
    
    # Can run either method
    [trigger_http, trigger_curl]
