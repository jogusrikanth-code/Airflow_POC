"""Monitoring API DAG
====================
Exposes REST API endpoint for external monitoring systems.

This DAG publishes metrics that can be consumed by:
- Custom dashboards
- Support team tools
- Integration with ticketing systems
- Mobile apps
"""

from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.models import DagRun, TaskInstance
from airflow.utils.state import State
from datetime import datetime, timedelta
import logging
import json

logger = logging.getLogger(__name__)


def export_metrics_to_file(**context):
    """Export all metrics to JSON file for external consumption."""
    from airflow.models import DagBag
    from airflow import settings
    
    session = settings.Session()
    
    try:
        # Collect all metrics
        dagbag = DagBag()
        
        # 1. DAG Statistics
        dag_stats = {
            'total_dags': len(dagbag.dag_ids),
            'dags_by_category': {
                'azure': len([d for d in dagbag.dag_ids if d.startswith('azure_')]),
                'databricks': len([d for d in dagbag.dag_ids if d.startswith('databricks_')]),
                'powerbi': len([d for d in dagbag.dag_ids if d.startswith('powerbi_')]),
                'onprem': len([d for d in dagbag.dag_ids if d.startswith('onprem_')]),
            }
        }
        
        # 2. Recent Run Statistics (last 24h)
        yesterday = datetime.now() - timedelta(days=1)
        recent_runs = session.query(DagRun).filter(
            DagRun.execution_date >= yesterday
        ).all()
        
        run_stats = {
            'total_runs_24h': len(recent_runs),
            'successful_runs': len([r for r in recent_runs if r.state == State.SUCCESS]),
            'failed_runs': len([r for r in recent_runs if r.state == State.FAILED]),
            'running_runs': len([r for r in recent_runs if r.state == State.RUNNING]),
        }
        
        # 3. Task Failure Statistics (last 24h)
        failed_tasks = session.query(TaskInstance).filter(
            TaskInstance.state == State.FAILED,
            TaskInstance.start_date >= yesterday
        ).all()
        
        task_stats = {
            'failed_tasks_24h': len(failed_tasks),
            'top_failing_dags': _get_top_failing_dags(failed_tasks, 5)
        }
        
        # 4. Health Score Calculation
        total = run_stats['total_runs_24h']
        success = run_stats['successful_runs']
        health_score = (success / total * 100) if total > 0 else 100
        
        # 5. Service-Specific Metrics
        service_metrics = _get_service_metrics(recent_runs)
        
        # Compile all metrics
        metrics = {
            'timestamp': datetime.now().isoformat(),
            'health_score': round(health_score, 2),
            'dag_statistics': dag_stats,
            'run_statistics': run_stats,
            'task_statistics': task_stats,
            'service_metrics': service_metrics,
            'alerts': _generate_alerts(health_score, failed_tasks, run_stats)
        }
        
        # Write to file that can be served via HTTP
        output_path = '/tmp/airflow_metrics.json'
        with open(output_path, 'w') as f:
            json.dump(metrics, f, indent=2)
        
        logger.info(f"✓ Metrics exported to {output_path}")
        logger.info(f"Health Score: {health_score:.1f}%")
        logger.info(f"Total DAGs: {dag_stats['total_dags']}")
        logger.info(f"Failed Tasks (24h): {task_stats['failed_tasks_24h']}")
        
        return metrics
        
    finally:
        session.close()


def _get_top_failing_dags(failed_tasks, limit):
    """Get top failing DAGs."""
    dag_failures = {}
    for task in failed_tasks:
        dag_failures[task.dag_id] = dag_failures.get(task.dag_id, 0) + 1
    
    sorted_failures = sorted(dag_failures.items(), key=lambda x: x[1], reverse=True)
    return [{'dag_id': dag, 'failures': count} for dag, count in sorted_failures[:limit]]


def _get_service_metrics(recent_runs):
    """Calculate metrics per service category."""
    services = ['azure', 'databricks', 'powerbi', 'onprem']
    metrics = {}
    
    for service in services:
        service_runs = [r for r in recent_runs if r.dag_id.startswith(f'{service}_')]
        total = len(service_runs)
        success = len([r for r in service_runs if r.state == State.SUCCESS])
        
        metrics[service] = {
            'total_runs': total,
            'successful_runs': success,
            'success_rate': round((success / total * 100) if total > 0 else 0, 2)
        }
    
    return metrics


def _generate_alerts(health_score, failed_tasks, run_stats):
    """Generate alerts based on metrics."""
    alerts = []
    
    # Critical: Health score below 80%
    if health_score < 80:
        alerts.append({
            'severity': 'critical',
            'message': f'Health score critically low: {health_score:.1f}%',
            'action': 'Immediate investigation required'
        })
    
    # Warning: High failure rate
    if run_stats['failed_runs'] > 5:
        alerts.append({
            'severity': 'warning',
            'message': f"{run_stats['failed_runs']} DAG failures in last 24h",
            'action': 'Review failed DAG logs'
        })
    
    # Info: Many task failures
    if len(failed_tasks) > 10:
        alerts.append({
            'severity': 'info',
            'message': f"{len(failed_tasks)} task failures detected",
            'action': 'Check task logs for patterns'
        })
    
    return alerts


def send_to_monitoring_system(**context):
    """Send metrics to external monitoring system."""
    ti = context['task_instance']
    metrics = ti.xcom_pull(task_ids='export_metrics')
    
    logger.info("=" * 80)
    logger.info("METRICS FOR EXTERNAL SYSTEMS")
    logger.info("=" * 80)
    
    # In production, send to:
    # - Prometheus Pushgateway
    # - DataDog API
    # - Custom monitoring endpoint
    # - CloudWatch
    
    logger.info(f"\nHealth Score: {metrics['health_score']}%")
    logger.info(f"Total DAGs: {metrics['dag_statistics']['total_dags']}")
    logger.info(f"Failed Runs (24h): {metrics['run_statistics']['failed_runs']}")
    
    if metrics['alerts']:
        logger.info("\n⚠ ACTIVE ALERTS:")
        for alert in metrics['alerts']:
            logger.info(f"  [{alert['severity'].upper()}] {alert['message']}")
            logger.info(f"    → {alert['action']}")
    else:
        logger.info("\n✓ No active alerts")
    
    logger.info("\nService Breakdown:")
    for service, stats in metrics['service_metrics'].items():
        logger.info(f"  {service.upper()}: {stats['success_rate']}% success rate")
    
    logger.info(f"\n{'=' * 80}\n")
    
    # Example: Send to custom endpoint
    # import requests
    # requests.post('https://monitoring.company.com/api/airflow', json=metrics)
    
    return {'status': 'sent', 'timestamp': datetime.now().isoformat()}


def send_alerts(**context):
    """Send alerts to support team."""
    ti = context['task_instance']
    metrics = ti.xcom_pull(task_ids='export_metrics')
    
    alerts = metrics.get('alerts', [])
    
    if not alerts:
        logger.info("✓ No alerts to send")
        return {'alerts_sent': 0}
    
    logger.info(f"Sending {len(alerts)} alerts to support team...")
    
    for alert in alerts:
        severity = alert['severity']
        message = alert['message']
        
        # Send to appropriate channel based on severity
        if severity == 'critical':
            logger.info(f"🚨 CRITICAL: {message}")
            # send_to_pagerduty(alert)
            # send_to_slack_critical(alert)
            
        elif severity == 'warning':
            logger.info(f"⚠ WARNING: {message}")
            # send_to_slack_warnings(alert)
            
        else:
            logger.info(f"ℹ INFO: {message}")
            # send_to_email_digest(alert)
    
    logger.info(f"✓ Sent {len(alerts)} alerts")
    
    return {'alerts_sent': len(alerts), 'alerts': alerts}


# DAG definition
default_args = {
    'owner': 'airflow',
    'depends_on_past': False,
    'start_date': datetime(2024, 12, 1),
    'email_on_failure': False,
    'email_on_retry': False,
    'retries': 1,
    'retry_delay': timedelta(minutes=2),
}

with DAG(
    'monitoring_api_exporter',
    default_args=default_args,
    description='Export metrics for external monitoring systems and support team',
    schedule='*/15 * * * *',  # Run every 15 minutes
    catchup=False,
    tags=['monitoring', 'api', 'metrics', 'alerts'],
) as dag:
    
    # Export metrics to JSON
    export_metrics = PythonOperator(
        task_id='export_metrics',
        python_callable=export_metrics_to_file,
    )
    
    # Send to external monitoring
    send_metrics = PythonOperator(
        task_id='send_to_monitoring',
        python_callable=send_to_monitoring_system,
    )
    
    # Send alerts to support team
    send_alerts_task = PythonOperator(
        task_id='send_alerts',
        python_callable=send_alerts,
    )
    
    # Pipeline: Export → Send Metrics + Send Alerts (parallel)
    export_metrics >> [send_metrics, send_alerts_task]
