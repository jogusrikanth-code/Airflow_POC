# Enterprise Monitoring & Support Setup

## Overview

This document outlines centralized monitoring options for organization-level Airflow deployment where support teams need visibility without accessing individual Airflow instances.

## 🎯 Recommended Enterprise Solutions

### 1. **Prometheus + Grafana (Recommended)**

**Best for:** Real-time metrics, alerting, and centralized dashboards

**Setup:**
```yaml
# Add to kubernetes/values.yaml
metrics:
  enabled: true
  serviceMonitor:
    enabled: true
  
# Airflow exports metrics on /admin/metrics
```

**Features:**
- Real-time DAG execution metrics
- Task success/failure rates
- Scheduler performance
- Resource utilization
- Custom alerts (Slack, PagerDuty, email)
- Multi-instance monitoring (all environments)

**Grafana Dashboards:**
- Pre-built Airflow dashboard: https://grafana.com/grafana/dashboards/15440
- Custom dashboard for your DAG categories

---

### 2. **Elasticsearch + Kibana (ELK Stack)**

**Best for:** Log aggregation and analysis

**Setup:**
```python
# Add to airflow.cfg
[elasticsearch]
host = elasticsearch.company.com:9200
log_id_template = {dag_id}-{task_id}-{execution_date}-{try_number}
```

**Features:**
- Centralized log storage
- Search across all DAG logs
- Log-based alerting
- Historical analysis
- Support team can search logs without Airflow access

---

### 3. **DataDog / New Relic (SaaS)**

**Best for:** Turnkey solution with minimal setup

**Setup:**
```bash
# Install DataDog agent in Kubernetes
helm install datadog-agent datadog/datadog
```

**Features:**
- Automatic Airflow integration
- Pre-built dashboards
- AI-powered anomaly detection
- Mobile app for support team
- Integration with incident management tools

---

### 4. **StatsD Integration (Built-in)**

**Best for:** Lightweight metrics export

Airflow has built-in StatsD support:

```python
# In airflow.cfg
[metrics]
statsd_on = True
statsd_host = statsd.company.com
statsd_port = 8125
statsd_prefix = airflow
```

Metrics can be visualized in:
- Grafana
- DataDog
- CloudWatch (AWS)
- Azure Monitor

---

## 🏢 Organization-Level Architecture

```
┌─────────────────────────────────────────────────────┐
│         Support Team Dashboard (Grafana)            │
│  - All Environments (Dev, QA, Prod)                │
│  - Real-time Status                                  │
│  - Alerting                                          │
└─────────────────────────────────────────────────────┘
                          ▲
                          │ (Prometheus Scrape)
                          │
        ┌─────────────────┼─────────────────┐
        │                 │                 │
┌───────▼───────┐ ┌───────▼───────┐ ┌───────▼───────┐
│  Airflow Dev  │ │  Airflow QA   │ │  Airflow Prod │
│  Namespace    │ │  Namespace    │ │  Namespace    │
└───────────────┘ └───────────────┘ └───────────────┘
```

---

## 📊 Key Metrics for Support Team

### DAG Metrics
- `airflow_dag_run_duration` - How long DAGs take
- `airflow_dag_run_failed` - Failure counts
- `airflow_dag_run_success` - Success counts
- `airflow_dag_run_running` - Currently running

### Task Metrics
- `airflow_task_instance_duration` - Task execution time
- `airflow_task_instance_failures` - Task failures
- `airflow_task_queue_length` - Backlog

### Scheduler Metrics
- `airflow_scheduler_heartbeat` - Scheduler health
- `airflow_executor_queue_size` - Work queue size
- `airflow_pool_slots_available` - Resource availability

---

## 🚨 Alerting Rules for Support Team

### Critical Alerts
```yaml
# Prometheus alerting rules
groups:
  - name: airflow_critical
    rules:
      - alert: AirflowSchedulerDown
        expr: up{job="airflow-scheduler"} == 0
        for: 5m
        
      - alert: HighDAGFailureRate
        expr: rate(airflow_dag_run_failed[1h]) > 0.5
        for: 10m
        
      - alert: LongRunningDAG
        expr: airflow_dag_run_duration > 7200  # 2 hours
        for: 5m
```

### Warning Alerts
- Task retry rate increasing
- Queue size growing
- Database connection issues
- Resource utilization high

---

## 🔐 Support Team Access Models

### Option A: Read-Only Airflow Access
```python
# Create viewer role for support team
from airflow.www.security import AirflowSecurityManager

VIEWER_PERMISSIONS = [
    'can_read on DAG',
    'can_read on Task Instance',
    'can_read on DAG Run',
]
```

### Option B: Separate Monitoring UI (Recommended)
- Support team uses Grafana/Kibana only
- No direct Airflow access needed
- Faster response times
- Better for compliance

### Option C: API-based Custom Dashboard
```python
# Build custom dashboard using Airflow REST API
GET /api/v1/dags
GET /api/v1/dags/{dag_id}/dagRuns
GET /api/v1/dags/{dag_id}/tasks
```

---

## 📱 Mobile/On-Call Support

### Options:
1. **PagerDuty Integration**
   ```python
   # In DAG callback
   on_failure_callback = send_to_pagerduty
   ```

2. **Slack Alerts**
   ```python
   from airflow.providers.slack.operators.slack_webhook import SlackWebhookOperator
   ```

3. **Microsoft Teams**
   ```python
   from airflow.providers.microsoft.teams.operators.teams_webhook import MSTeamsWebhookOperator
   ```

4. **Email Digest**
   - Daily summary of all failures
   - Weekly health report

---

## 🎯 Implementation Recommendation

For your organization, I recommend:

### Phase 1: Quick Win (Week 1)
1. ✅ Enable StatsD metrics in Airflow
2. ✅ Deploy Grafana with Airflow dashboard
3. ✅ Set up Slack alerts for critical failures

### Phase 2: Enhanced Monitoring (Week 2-3)
1. Deploy Prometheus for metric collection
2. Configure alerting rules
3. Create custom dashboards for each service (Azure, Databricks, etc.)

### Phase 3: Enterprise Features (Month 2)
1. Add ELK stack for log aggregation
2. Implement API-based custom dashboard
3. Mobile app integration
4. Multi-environment monitoring

---

## 🚀 Quick Start: Grafana Dashboard

I can create:
1. `monitoring/grafana-dashboard.json` - Pre-configured dashboard
2. `monitoring/prometheus-config.yaml` - Prometheus scrape config
3. `monitoring/alerting-rules.yaml` - Support team alerts
4. `dags/monitoring_api_dag.py` - Export metrics via REST API

---

## 📞 Support Team Workflow

```
1. Alert fires → PagerDuty/Slack
2. Support opens Grafana dashboard
3. Identifies failed DAG/service
4. Views logs in Kibana (optional)
5. Escalates to data engineering if needed
```

**Key Benefit:** Support team never needs Airflow credentials or training!

---

## Next Steps

Would you like me to:
1. ✅ Set up Grafana dashboard configuration?
2. ✅ Create Prometheus metrics exporter?
3. ✅ Add Slack/Teams alerting to DAGs?
4. ✅ Create REST API monitoring endpoint?
5. ✅ All of the above?
