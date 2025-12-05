"""Master Monitoring Dashboard DAG
====================================
Centralized monitoring for all data pipelines in the POC.

This DAG provides:
- Status overview of all DAGs
- Recent task failures
- Connection health checks
- Data pipeline metrics
- Summary reports
"""

from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.models import DagRun, TaskInstance
from airflow.utils.state import State
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)


def check_dag_health(**context):
    """Check health status of all DAGs."""
    from airflow.models import DagBag
    
    logger.info("=" * 80)
    logger.info("DAG HEALTH CHECK")
    logger.info("=" * 80)
    
    dagbag = DagBag()
    
    dag_categories = {
        'Azure': [],
        'Databricks': [],
        'Power BI': [],
        'On-Prem': [],
        'Other': []
    }
    
    # Categorize DAGs
    for dag_id in dagbag.dag_ids:
        if dag_id.startswith('azure_'):
            dag_categories['Azure'].append(dag_id)
        elif dag_id.startswith('databricks_'):
            dag_categories['Databricks'].append(dag_id)
        elif dag_id.startswith('powerbi_'):
            dag_categories['Power BI'].append(dag_id)
        elif dag_id.startswith('onprem_'):
            dag_categories['On-Prem'].append(dag_id)
        else:
            dag_categories['Other'].append(dag_id)
    
    # Print categorized DAGs
    total_dags = 0
    for category, dags in dag_categories.items():
        if dags:
            logger.info(f"\n{category} DAGs ({len(dags)}):")
            for dag_id in sorted(dags):
                logger.info(f"  ✓ {dag_id}")
                total_dags += 1
    
    logger.info(f"\n{'=' * 80}")
    logger.info(f"TOTAL DAGS: {total_dags}")
    logger.info(f"{'=' * 80}\n")
    
    return {
        'total_dags': total_dags,
        'categories': {k: len(v) for k, v in dag_categories.items()}
    }


def check_recent_failures(**context):
    """Check for recent task failures."""
    from airflow import settings
    
    logger.info("=" * 80)
    logger.info("RECENT FAILURES (Last 24 Hours)")
    logger.info("=" * 80)
    
    session = settings.Session()
    
    try:
        # Get failed tasks from last 24 hours
        yesterday = datetime.now() - timedelta(days=1)
        
        failed_tasks = session.query(TaskInstance).filter(
            TaskInstance.state == State.FAILED,
            TaskInstance.start_date >= yesterday
        ).order_by(TaskInstance.start_date.desc()).limit(10).all()
        
        if not failed_tasks:
            logger.info("\n✓ No failures in the last 24 hours\n")
            return {'failures': 0}
        
        logger.info(f"\n⚠ Found {len(failed_tasks)} failed tasks:\n")
        
        for task in failed_tasks:
            logger.info(f"  DAG: {task.dag_id}")
            logger.info(f"  Task: {task.task_id}")
            logger.info(f"  Time: {task.start_date}")
            logger.info(f"  Duration: {task.duration}s")
            logger.info(f"  {'-' * 70}")
        
        logger.info(f"\n{'=' * 80}\n")
        
        return {'failures': len(failed_tasks)}
        
    finally:
        session.close()


def check_connection_health(**context):
    """Check health of all configured connections."""
    from airflow.models import Connection
    from airflow import settings
    
    logger.info("=" * 80)
    logger.info("CONNECTION HEALTH CHECK")
    logger.info("=" * 80)
    
    session = settings.Session()
    
    try:
        connections = session.query(Connection).all()
        
        conn_types = {}
        for conn in connections:
            conn_type = conn.conn_type or 'unknown'
            if conn_type not in conn_types:
                conn_types[conn_type] = []
            conn_types[conn_type].append(conn.conn_id)
        
        logger.info(f"\nConfigured Connections ({len(connections)}):\n")
        
        for conn_type, conn_ids in sorted(conn_types.items()):
            logger.info(f"  {conn_type.upper()} ({len(conn_ids)}):")
            for conn_id in sorted(conn_ids):
                logger.info(f"    • {conn_id}")
        
        logger.info(f"\n{'=' * 80}\n")
        
        return {
            'total_connections': len(connections),
            'by_type': {k: len(v) for k, v in conn_types.items()}
        }
        
    finally:
        session.close()


def check_recent_runs(**context):
    """Check recent DAG runs status."""
    from airflow import settings
    
    logger.info("=" * 80)
    logger.info("RECENT DAG RUNS (Last 7 Days)")
    logger.info("=" * 80)
    
    session = settings.Session()
    
    try:
        # Get runs from last 7 days
        week_ago = datetime.now() - timedelta(days=7)
        
        recent_runs = session.query(DagRun).filter(
            DagRun.execution_date >= week_ago
        ).order_by(DagRun.execution_date.desc()).limit(20).all()
        
        if not recent_runs:
            logger.info("\nNo recent runs found\n")
            return {'runs': 0}
        
        # Count by state
        state_counts = {}
        for run in recent_runs:
            state = run.state or 'unknown'
            state_counts[state] = state_counts.get(state, 0) + 1
        
        logger.info(f"\nLast {len(recent_runs)} runs:\n")
        
        for state, count in sorted(state_counts.items()):
            emoji = '✓' if state == 'success' else '⚠' if state == 'failed' else '○'
            logger.info(f"  {emoji} {state.upper()}: {count}")
        
        logger.info("\nRecent Runs:")
        for run in recent_runs[:10]:
            emoji = '✓' if run.state == 'success' else '✗' if run.state == 'failed' else '○'
            logger.info(f"  {emoji} {run.dag_id} - {run.state} - {run.execution_date}")
        
        logger.info(f"\n{'=' * 80}\n")
        
        return {
            'total_runs': len(recent_runs),
            'by_state': state_counts
        }
        
    finally:
        session.close()


def generate_summary_report(**context):
    """Generate overall summary report."""
    ti = context['task_instance']
    
    # Pull results from previous tasks
    dag_health = ti.xcom_pull(task_ids='check_dag_health')
    failures = ti.xcom_pull(task_ids='check_recent_failures')
    connections = ti.xcom_pull(task_ids='check_connection_health')
    recent_runs = ti.xcom_pull(task_ids='check_recent_runs')
    
    logger.info("=" * 80)
    logger.info("SUMMARY REPORT")
    logger.info("=" * 80)
    
    logger.info("\n📊 OVERVIEW:")
    logger.info(f"  • Total DAGs: {dag_health.get('total_dags', 0)}")
    logger.info(f"  • Total Connections: {connections.get('total_connections', 0)}")
    logger.info(f"  • Recent Runs (7 days): {recent_runs.get('total_runs', 0)}")
    logger.info(f"  • Recent Failures (24h): {failures.get('failures', 0)}")
    
    logger.info("\n📁 DAG CATEGORIES:")
    for category, count in dag_health.get('categories', {}).items():
        if count > 0:
            logger.info(f"  • {category}: {count}")
    
    logger.info("\n🔌 CONNECTIONS BY TYPE:")
    for conn_type, count in connections.get('by_type', {}).items():
        logger.info(f"  • {conn_type}: {count}")
    
    logger.info("\n📈 RUN STATUS (7 days):")
    for state, count in recent_runs.get('by_state', {}).items():
        logger.info(f"  • {state}: {count}")
    
    # Health score
    total_runs = recent_runs.get('total_runs', 0)
    success_runs = recent_runs.get('by_state', {}).get('success', 0)
    health_score = (success_runs / total_runs * 100) if total_runs > 0 else 0
    
    logger.info(f"\n💚 HEALTH SCORE: {health_score:.1f}%")
    
    logger.info(f"\n{'=' * 80}")
    logger.info(f"Report generated: {datetime.now()}")
    logger.info(f"{'=' * 80}\n")
    
    return {
        'timestamp': datetime.now().isoformat(),
        'health_score': health_score,
        'summary': {
            'dags': dag_health,
            'failures': failures,
            'connections': connections,
            'runs': recent_runs
        }
    }


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
    'master_monitoring_dashboard',
    default_args=default_args,
    description='Centralized monitoring dashboard for all data pipelines',
    schedule='0 */4 * * *',  # Run every 4 hours
    catchup=False,
    tags=['monitoring', 'dashboard', 'health-check'],
) as dag:
    
    # Check DAG health
    dag_health = PythonOperator(
        task_id='check_dag_health',
        python_callable=check_dag_health,
    )
    
    # Check recent failures
    recent_failures = PythonOperator(
        task_id='check_recent_failures',
        python_callable=check_recent_failures,
    )
    
    # Check connection health
    connection_health = PythonOperator(
        task_id='check_connection_health',
        python_callable=check_connection_health,
    )
    
    # Check recent runs
    recent_runs = PythonOperator(
        task_id='check_recent_runs',
        python_callable=check_recent_runs,
    )
    
    # Generate summary report
    summary = PythonOperator(
        task_id='generate_summary_report',
        python_callable=generate_summary_report,
    )
    
    # Run all checks in parallel, then generate summary
    [dag_health, recent_failures, connection_health, recent_runs] >> summary
