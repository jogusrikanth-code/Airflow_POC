# DAG Monitoring Guide for Apache Airflow

## 🎯 Complete DAG Monitoring Setup

**Last Updated:** December 4, 2025  
**Cluster:** aks-airflow-poc  
**Airflow Version:** 3.0.2

---

## Overview

Your Airflow deployment has **3 layers of DAG monitoring**:

1. **Airflow UI** - Real-time DAG status and logs
2. **Azure Monitor** - Historical log analysis and infrastructure metrics
3. **StatsD/Prometheus** - Real-time DAG performance metrics

---

## 📊 Layer 1: Airflow UI Monitoring

### Access
- **URL:** http://51.8.246.115
- **Credentials:** admin / admin123

### Key Features

#### 1. DAG Dashboard
- **Path:** Home (main page)
- **Shows:**
  - All DAGs with pause/unpause status
  - Recent runs (success/failed/running)
  - Next scheduled run time
  - Tags for filtering

#### 2. DAG Detail View
Click on any DAG name to see:
- **Grid View:** Visual timeline of all task instances
- **Graph View:** DAG structure and dependencies
- **Calendar View:** Historical run patterns
- **Task Duration:** Performance trends over time
- **Task Tries:** Retry patterns
- **Landing Times:** When tasks complete
- **Gantt Chart:** Task execution timeline
- **Code:** View the DAG source code

#### 3. Monitor Specific DAG Runs

**Steps:**
1. Click on DAG name (e.g., `azure_blob_copy`)
2. Select "Grid" view
3. Click on any colored square (task instance)
4. View:
   - **Log:** Full execution logs
   - **Details:** Start/end time, duration
   - **Rendered:** Template values used
   - **XCom:** Data passed between tasks

#### 4. Filter DAGs

**By Status:**
- Active DAGs only
- Paused DAGs only
- Recently modified

**By Tags:**
- Click tag badges to filter
- Example: `azure`, `databricks`, `etl`

#### 5. Browse Menu Options

**Browse → DAG Runs:**
- All DAG executions across all DAGs
- Filter by date range, status, DAG ID
- Bulk delete old runs

**Browse → Task Instances:**
- All task executions across all DAGs
- Filter by task status (success/failed/running/queued)
- Find bottlenecks

**Browse → DAG Import Errors:**
- Shows DAGs that failed to parse
- Python syntax errors
- Import errors
- Very useful for debugging

---

## 🔍 Layer 2: Azure Monitor for DAG Logs

### Access
1. **Azure Portal:** https://portal.azure.com
2. **Navigate to:** aks-airflow-poc
3. **Click:** Logs (under Monitoring)

### Pre-Built KQL Queries

#### Query 1: All DAG Executions (Last 24 Hours)
```kusto
ContainerLog
| where Namespace == "airflow"
| where ContainerName contains "scheduler"
| where LogEntry contains "DAG" or LogEntry contains "Task"
| where TimeGenerated > ago(24h)
| project TimeGenerated, LogEntry
| order by TimeGenerated desc
| take 100
```

#### Query 2: Failed DAG Runs
```kusto
ContainerLog
| where Namespace == "airflow"
| where LogEntry contains "failed" or LogEntry contains "ERROR"
| where TimeGenerated > ago(24h)
| project TimeGenerated, ContainerName, LogEntry
| order by TimeGenerated desc
```

#### Query 3: Monitor Specific DAG (azure_blob_copy)
```kusto
ContainerLog
| where Namespace == "airflow"
| where LogEntry contains "azure_blob_copy"
| where TimeGenerated > ago(7d)
| project TimeGenerated, LogEntry
| order by TimeGenerated desc
```

#### Query 4: DAG Execution Duration Trends
```kusto
ContainerLog
| where Namespace == "airflow"
| where LogEntry contains "duration"
| where TimeGenerated > ago(7d)
| parse LogEntry with * "duration=" Duration:double *
| summarize AvgDuration = avg(Duration), MaxDuration = max(Duration) by bin(TimeGenerated, 1h)
| render timechart
```

#### Query 5: Task Retry Patterns
```kusto
ContainerLog
| where Namespace == "airflow"
| where LogEntry contains "retry"
| where TimeGenerated > ago(7d)
| summarize RetryCount = count() by bin(TimeGenerated, 1h)
| render timechart
```

#### Query 6: Count DAG Runs by Status
```kusto
ContainerLog
| where Namespace == "airflow"
| where LogEntry contains "DAG Run"
| where TimeGenerated > ago(24h)
| parse LogEntry with * "state=" State " " *
| summarize Count = count() by State
| render piechart
```

### Save Queries for Quick Access

1. Run any query above
2. Click **Save** → **Save as query**
3. Give it a name (e.g., "Failed DAG Runs - Last 24h")
4. Access later from **Saved Queries** tab

---

## 📈 Layer 3: StatsD Metrics (Advanced)

### Current Setup

✅ **StatsD Exporter:** Running (`airflow-statsd` deployment)  
✅ **Metrics Port:** 9102 (Prometheus format)  
✅ **StatsD Port:** 9125 (UDP)

### Available Metrics

Airflow automatically exports these metrics:

**DAG Metrics:**
- `airflow_dag_processing_last_duration` - Time to parse DAG files
- `airflow_dagrun_duration_<dag_id>` - DAG execution time
- `airflow_dagrun_schedule_delay_<dag_id>` - Scheduling lag
- `airflow_task_removed_from_dag` - Tasks that disappeared
- `airflow_task_restored_to_dag` - Tasks that reappeared

**Task Metrics:**
- `airflow_ti_failures` - Task instance failures
- `airflow_ti_successes` - Task instance successes
- `airflow_operator_failures_<operator>` - Failures by operator type
- `airflow_operator_successes_<operator>` - Successes by operator type

**Scheduler Metrics:**
- `airflow_scheduler_heartbeat` - Scheduler liveness
- `airflow_scheduler_tasks_executable` - Tasks ready to run
- `airflow_scheduler_tasks_running` - Currently executing tasks
- `airflow_scheduler_tasks_starving` - Tasks waiting too long

**Executor Metrics:**
- `airflow_executor_open_slots` - Available worker capacity
- `airflow_executor_queued_tasks` - Tasks waiting for execution
- `airflow_executor_running_tasks` - Currently running tasks

### Access Metrics Directly

```powershell
# Port-forward to access metrics
kubectl port-forward svc/airflow-statsd 9102:9102 -n airflow

# Then open browser: http://localhost:9102/metrics
# You'll see Prometheus-format metrics
```

### Example Metrics Output
```
# HELP airflow_dagrun_duration_success DAG run duration
# TYPE airflow_dagrun_duration_success histogram
airflow_dagrun_duration_success{dag_id="azure_blob_copy"} 45.2

# HELP airflow_ti_successes Task instance successes
# TYPE airflow_ti_successes counter
airflow_ti_successes{dag_id="azure_blob_copy",task_id="copy_files"} 5
```

---

## 🔔 Setting Up Alerts

### Option 1: Azure Monitor Alerts (Recommended)

#### Alert 1: DAG Failure Alert

**Create Alert:**
```powershell
# Create action group (one-time setup)
az monitor action-group create \
  --resource-group bi_lakehouse_dev_rg \
  --name airflow-dag-alerts \
  --short-name dagalerts \
  --email-receiver name="Team" email="your-team@example.com"
```

**Create Log Query Alert:**
1. Go to: Azure Portal → aks-airflow-poc → Alerts → Create alert rule
2. **Condition:** Custom log search
3. **Query:**
   ```kusto
   ContainerLog
   | where Namespace == "airflow"
   | where LogEntry contains "failed" or LogEntry contains "ERROR"
   | where LogEntry contains "DAG"
   | where TimeGenerated > ago(5m)
   | summarize FailureCount = count()
   ```
4. **Alert logic:** 
   - When FailureCount is greater than 0
   - Evaluation frequency: Every 5 minutes
5. **Actions:** Select `airflow-dag-alerts` action group
6. **Alert details:** Name it "DAG Failure Alert"

#### Alert 2: Long-Running DAG

**Query:**
```kusto
ContainerLog
| where Namespace == "airflow"
| where LogEntry contains "Running for"
| parse LogEntry with * "Running for " Duration:double " seconds" *
| where Duration > 3600  // Alert if running > 1 hour
| project TimeGenerated, LogEntry
```

#### Alert 3: DAG Import Errors

**Query:**
```kusto
ContainerLog
| where Namespace == "airflow"
| where ContainerName contains "dag-processor"
| where LogEntry contains "Failed to import"
| where TimeGenerated > ago(5m)
```

### Option 2: Airflow Built-in Email Alerts

**Edit your DAG to include email notifications:**

```python
from airflow import DAG
from airflow.operators.python import PythonOperator
from datetime import datetime

default_args = {
    'owner': 'airflow',
    'email': ['your-team@example.com'],
    'email_on_failure': True,
    'email_on_retry': True,
    'email_on_success': False,  # Usually too noisy
    'retries': 2,
}

with DAG(
    dag_id='azure_blob_copy',
    default_args=default_args,
    schedule=None,
    catchup=False,
) as dag:
    # Your tasks here
    pass
```

**Configure SMTP in Helm values:**

```yaml
# Add to values-aks-airflow.yaml
config:
  smtp:
    smtp_host: smtp.office365.com
    smtp_port: 587
    smtp_starttls: true
    smtp_ssl: false
    smtp_user: airflow@yourcompany.com
    smtp_password: your-password
    smtp_mail_from: airflow@yourcompany.com
```

**Apply:**
```powershell
helm upgrade airflow apache-airflow/airflow \
  --namespace airflow \
  --reuse-values \
  --set config.smtp.smtp_host=smtp.office365.com \
  --set config.smtp.smtp_port=587 \
  --set config.smtp.smtp_mail_from=airflow@yourcompany.com
```

---

## 📱 Quick Monitoring Commands

### Check DAG Status via CLI

```powershell
# List all DAGs
kubectl exec deployment/airflow-scheduler -n airflow -- airflow dags list

# Get DAG run status
kubectl exec deployment/airflow-scheduler -n airflow -- \
  airflow dags list-runs -d azure_blob_copy

# Get task instance status
kubectl exec deployment/airflow-scheduler -n airflow -- \
  airflow tasks list azure_blob_copy

# Test a DAG (dry run)
kubectl exec deployment/airflow-scheduler -n airflow -- \
  airflow dags test azure_blob_copy 2024-12-04
```

### Check Recent Logs

```powershell
# Scheduler logs (shows DAG scheduling activity)
kubectl logs deployment/airflow-scheduler -n airflow --tail=100 | Select-String "azure_blob_copy"

# DAG processor logs (shows DAG parsing)
kubectl logs deployment/airflow-dag-processor -n airflow -c dag-processor --tail=100
```

---

## 📊 Custom DAG Monitoring Dashboard

### HTML Dashboard (Already Available)

**Location:** `monitoring/azure-monitor-alternative.html`

**Features:**
- Real-time DAG count
- Success rate (last 24h)
- Recent failures
- Active vs paused DAGs

**Access:**
```powershell
Start-Process "C:\Users\sjogu\OneDrive - Spencer Gifts LLC\Documents\Srikanth_Jogu\Airflow_POC\monitoring\azure-monitor-alternative.html"
```

**Configure:**
- URL: `http://51.8.246.115`
- Username: `admin`
- Password: `admin123`

---

## 🎯 Monitoring Checklist

### Daily Monitoring
- [ ] Check Airflow UI for failed DAG runs
- [ ] Review any email alerts received
- [ ] Check Azure Monitor for error spikes

### Weekly Monitoring
- [ ] Review DAG execution duration trends
- [ ] Check for import errors
- [ ] Verify all scheduled DAGs are running
- [ ] Review task retry patterns

### Monthly Monitoring
- [ ] Analyze DAG performance over time
- [ ] Optimize slow-running DAGs
- [ ] Clean up old DAG runs (if needed)
- [ ] Review and update alerts

---

## 🔧 Troubleshooting DAG Issues

### DAG Not Appearing in UI

**Check:**
1. Browse → DAG Import Errors (shows Python errors)
2. DAG processor logs:
   ```powershell
   kubectl logs deployment/airflow-dag-processor -n airflow -c dag-processor --tail=200
   ```
3. Verify DAG file syntax:
   ```powershell
   python dags/azure/azure_blob_copy_generic.py
   ```

### DAG Not Scheduling

**Check:**
1. Is DAG paused? (toggle in UI)
2. Is schedule correct? (check `schedule` parameter)
3. Scheduler logs:
   ```powershell
   kubectl logs deployment/airflow-scheduler -n airflow --tail=200
   ```
4. Scheduler is running:
   ```powershell
   kubectl get pods -n airflow | Select-String "scheduler"
   ```

### Task Stuck in "Queued"

**Check:**
1. Are there available executor slots?
   ```powershell
   kubectl get pods -n airflow | Select-String "worker"
   ```
2. Check task dependencies (Graph view in UI)
3. Scheduler logs for errors

### Task Failed

**Steps:**
1. Click on failed task in UI → View logs
2. Check Azure Monitor for full traceback
3. Review task code for errors
4. Check Airflow connections (Admin → Connections)

---

## 📚 Additional Resources

### Airflow REST API
Access programmatically: `http://51.8.246.115/api/v1/`

**Example:**
```powershell
# Get DAG runs
Invoke-RestMethod -Uri "http://51.8.246.115/api/v1/dags/azure_blob_copy/dagRuns" `
  -Method Get `
  -Headers @{Authorization="Basic YWRtaW46YWRtaW4xMjM="} # Base64 of admin:admin123
```

### Monitoring Best Practices

1. **Set realistic SLAs** - Don't alert on every minor issue
2. **Use DAG-level callbacks** - For custom monitoring logic
3. **Tag your DAGs** - For easier filtering and organization
4. **Document failures** - Add comments to failed runs explaining root cause
5. **Regular cleanup** - Delete old DAG runs to keep database lean

---

## 🎉 Summary

You have **three powerful monitoring layers**:

| Layer | Best For | Access |
|-------|----------|--------|
| **Airflow UI** | Real-time DAG status, logs, manual triggering | http://51.8.246.115 |
| **Azure Monitor** | Historical analysis, alerting, log queries | Azure Portal → Insights/Logs |
| **StatsD Metrics** | Performance metrics, Grafana dashboards | Port-forward or Prometheus |

**Recommended Workflow:**
1. Use **Airflow UI** for daily monitoring
2. Set up **Azure Monitor alerts** for failures
3. Use **KQL queries** for analysis and reporting
4. Access **HTML dashboard** for quick status checks

---

**Last Updated:** December 4, 2025  
**Status:** ✅ All monitoring layers operational
