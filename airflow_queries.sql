-- ============================================================================
-- Airflow Database Queries - Useful SQL for Debugging & Monitoring
-- ============================================================================
-- Connection: localhost:5432, Database: airflow, User: airflow
-- Run these queries in VS Code using the PostgreSQL extension
-- ============================================================================

-- ============================================================================
-- 1. VIEW ALL DAGS
-- ============================================================================
-- See all DAGs in your Airflow instance with their status
SELECT 
    dag_id,
    is_paused,
    owners,
    description,
    fileloc
FROM dag
ORDER BY dag_id;


-- ============================================================================
-- 2. RECENT DAG RUNS (Last 10)
-- ============================================================================
-- Check the most recent DAG executions and their status
SELECT 
    dag_id,
    run_id,
    execution_date,
    start_date,
    end_date,
    state,
    run_type
FROM dag_run
ORDER BY execution_date DESC
LIMIT 10;


-- ============================================================================
-- 3. DAG RUN SUCCESS RATE
-- ============================================================================
-- Calculate success rate for each DAG
SELECT 
    dag_id,
    COUNT(*) as total_runs,
    SUM(CASE WHEN state = 'success' THEN 1 ELSE 0 END) as successful_runs,
    SUM(CASE WHEN state = 'failed' THEN 1 ELSE 0 END) as failed_runs,
    ROUND(100.0 * SUM(CASE WHEN state = 'success' THEN 1 ELSE 0 END) / COUNT(*), 2) as success_rate_percent
FROM dag_run
GROUP BY dag_id
ORDER BY dag_id;


-- ============================================================================
-- 4. FAILED TASKS (Most Recent)
-- ============================================================================
-- Find tasks that failed recently for troubleshooting
SELECT 
    dag_id,
    task_id,
    execution_date,
    state,
    try_number,
    duration,
    start_date,
    end_date
FROM task_instance
WHERE state = 'failed'
ORDER BY execution_date DESC
LIMIT 20;


-- ============================================================================
-- 5. TASK EXECUTION STATISTICS
-- ============================================================================
-- See how many times each task has been in each state
SELECT 
    dag_id,
    task_id,
    state,
    COUNT(*) as count,
    AVG(duration) as avg_duration_seconds
FROM task_instance
GROUP BY dag_id, task_id, state
ORDER BY dag_id, task_id, state;


-- ============================================================================
-- 6. SLOW RUNNING TASKS (Top 20)
-- ============================================================================
-- Identify tasks that take the longest to execute
SELECT 
    dag_id,
    task_id,
    execution_date,
    duration as duration_seconds,
    ROUND(duration / 60.0, 2) as duration_minutes,
    state
FROM task_instance
WHERE duration IS NOT NULL
ORDER BY duration DESC
LIMIT 20;


-- ============================================================================
-- 7. CURRENTLY RUNNING TASKS
-- ============================================================================
-- See what's running right now
SELECT 
    dag_id,
    task_id,
    execution_date,
    start_date,
    state,
    hostname,
    try_number
FROM task_instance
WHERE state = 'running'
ORDER BY start_date DESC;


-- ============================================================================
-- 8. TASK RETRY ANALYSIS
-- ============================================================================
-- Find tasks that required multiple attempts
SELECT 
    dag_id,
    task_id,
    execution_date,
    try_number,
    state,
    start_date,
    end_date
FROM task_instance
WHERE try_number > 1
ORDER BY execution_date DESC, try_number DESC
LIMIT 20;


-- ============================================================================
-- 9. DAG SCHEDULE INFO
-- ============================================================================
-- View scheduling information for all DAGs
SELECT 
    dag_id,
    schedule_interval,
    is_paused,
    is_active,
    next_dagrun,
    next_dagrun_create_after
FROM dag
ORDER BY dag_id;


-- ============================================================================
-- 10. TASK INSTANCE COUNT BY DAG
-- ============================================================================
-- See how many task instances exist per DAG
SELECT 
    dag_id,
    COUNT(*) as total_task_instances,
    COUNT(DISTINCT execution_date) as unique_dag_runs,
    COUNT(DISTINCT task_id) as unique_tasks
FROM task_instance
GROUP BY dag_id
ORDER BY total_task_instances DESC;


-- ============================================================================
-- 11. RECENT TASK FAILURES WITH DETAILS
-- ============================================================================
-- Get detailed information about recent failures
SELECT 
    ti.dag_id,
    ti.task_id,
    ti.execution_date,
    ti.state,
    ti.try_number,
    ti.start_date,
    ti.end_date,
    ti.duration,
    ti.hostname,
    dr.run_type
FROM task_instance ti
JOIN dag_run dr ON ti.dag_id = dr.dag_id 
    AND ti.execution_date = dr.execution_date
WHERE ti.state IN ('failed', 'up_for_retry')
ORDER BY ti.start_date DESC
LIMIT 20;


-- ============================================================================
-- 12. TASK DURATION TRENDS (by DAG)
-- ============================================================================
-- Analyze average task duration over time
SELECT 
    dag_id,
    task_id,
    DATE(execution_date) as execution_day,
    COUNT(*) as runs,
    AVG(duration) as avg_duration_seconds,
    MIN(duration) as min_duration_seconds,
    MAX(duration) as max_duration_seconds
FROM task_instance
WHERE duration IS NOT NULL
GROUP BY dag_id, task_id, DATE(execution_date)
ORDER BY dag_id, task_id, execution_day DESC;


-- ============================================================================
-- 13. CONNECTION CONFIGURATION
-- ============================================================================
-- List all configured Airflow connections (passwords are encrypted)
SELECT 
    conn_id,
    conn_type,
    host,
    schema,
    login,
    port,
    is_encrypted,
    is_extra_encrypted
FROM connection
ORDER BY conn_id;


-- ============================================================================
-- 14. VARIABLES
-- ============================================================================
-- View all Airflow variables
SELECT 
    key,
    val,
    is_encrypted
FROM variable
ORDER BY key;


-- ============================================================================
-- 15. XCOM DATA (Recent)
-- ============================================================================
-- Check XCom data passed between tasks
SELECT 
    dag_id,
    task_id,
    execution_date,
    key,
    value,
    timestamp
FROM xcom
ORDER BY timestamp DESC
LIMIT 50;


-- ============================================================================
-- 16. DAG RUNS BY STATE
-- ============================================================================
-- Count DAG runs grouped by state
SELECT 
    dag_id,
    state,
    COUNT(*) as count
FROM dag_run
GROUP BY dag_id, state
ORDER BY dag_id, state;


-- ============================================================================
-- 17. TASK INSTANCES WAITING FOR DEPENDENCIES
-- ============================================================================
-- Find tasks stuck waiting for upstream tasks
SELECT 
    dag_id,
    task_id,
    execution_date,
    state,
    try_number,
    start_date
FROM task_instance
WHERE state IN ('upstream_failed', 'skipped')
ORDER BY execution_date DESC
LIMIT 20;


-- ============================================================================
-- 18. TASK INSTANCE STATES OVER TIME
-- ============================================================================
-- See task state distribution by date
SELECT 
    DATE(execution_date) as execution_day,
    state,
    COUNT(*) as count
FROM task_instance
WHERE execution_date >= CURRENT_DATE - INTERVAL '7 days'
GROUP BY DATE(execution_date), state
ORDER BY execution_day DESC, count DESC;


-- ============================================================================
-- 19. LONGEST RUNNING DAG RUNS
-- ============================================================================
-- Find DAG runs that took the longest time
SELECT 
    dag_id,
    run_id,
    execution_date,
    start_date,
    end_date,
    EXTRACT(EPOCH FROM (end_date - start_date)) as duration_seconds,
    ROUND(EXTRACT(EPOCH FROM (end_date - start_date)) / 60.0, 2) as duration_minutes,
    state
FROM dag_run
WHERE end_date IS NOT NULL
ORDER BY duration_seconds DESC
LIMIT 20;


-- ============================================================================
-- 20. AIRFLOW VERSION & METADATA
-- ============================================================================
-- Check Airflow version from the database
SELECT * FROM alembic_version;

-- Database size
SELECT 
    pg_size_pretty(pg_database_size('airflow')) as database_size;

-- Table sizes
SELECT 
    schemaname,
    tablename,
    pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) as size
FROM pg_tables
WHERE schemaname = 'public'
ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC
LIMIT 10;


-- ============================================================================
-- TIPS FOR USING THESE QUERIES:
-- ============================================================================
-- 1. Select the query you want to run and execute it (Ctrl+Enter in VS Code)
-- 2. Modify the LIMIT values to see more/fewer results
-- 3. Adjust date filters to focus on specific time ranges
-- 4. Combine WHERE clauses to filter by specific DAGs or tasks
-- 5. Use these queries to debug issues, monitor performance, and understand workflow behavior
-- ============================================================================
