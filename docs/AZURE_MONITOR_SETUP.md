# Azure Monitor Setup Guide for Airflow

## ✅ Azure Monitor Container Insights - ENABLED

**Status:** Successfully enabled on December 4, 2025

**Log Analytics Workspace:** `airflow-logs-workspace`  
**Resource Group:** `bi_lakehouse_dev_rg`  
**Workspace ID:** `8e2e2da2-bb0c-40ec-ab8b-73ac9c6b09ca`  
**Data Retention:** 30 days (configurable)

### Quick Access

1. **Azure Portal:** https://portal.azure.com
2. **Navigate to:** `aks-airflow-poc` cluster
3. **Click:** "Insights" under "Monitoring"

### What's Monitored

✅ **Cluster Metrics**
- Node CPU, memory, disk usage
- Cluster health status
- Resource utilization trends

✅ **Pod & Container Metrics**
- All Airflow pods (scheduler, triggerer, dag-processor, api-server)
- PostgreSQL database pod
- Worker pods (task execution)
- Real-time resource consumption

✅ **Logs Collection**
- Container stdout/stderr logs
- Kubernetes events
- Application logs from all pods

✅ **Performance Insights**
- Slowest containers
- Failed pod restarts
- OOM (Out of Memory) events

---

## 📊 Using Azure Monitor Container Insights

### 1. View Cluster Overview

**Path:** AKS Cluster → Insights → Cluster

Shows:
- Node status and health
- Resource utilization graphs
- Active alerts

### 2. View Pod Metrics

**Path:** AKS Cluster → Insights → Containers

Filter by:
- Namespace: `airflow`
- Container name: `scheduler`, `dag-processor`, etc.

View:
- CPU usage trends
- Memory consumption
- Restarts count
- Status (Running/Failed)

### 3. Query Logs with KQL

**Path:** AKS Cluster → Logs

**Example Queries:**

```kusto
// All Airflow scheduler logs (last hour)
ContainerLog
| where Namespace == "airflow"
| where ContainerName contains "scheduler"
| where TimeGenerated > ago(1h)
| project TimeGenerated, LogEntry
| order by TimeGenerated desc

// Failed DAG runs
ContainerLog
| where Namespace == "airflow"
| where LogEntry contains "failed" or LogEntry contains "error"
| where TimeGenerated > ago(24h)
| project TimeGenerated, ContainerName, LogEntry
| order by TimeGenerated desc

// Pod restarts in last 24 hours
KubePodInventory
| where Namespace == "airflow"
| where ContainerRestartCount > 0
| where TimeGenerated > ago(24h)
| summarize RestartCount = max(ContainerRestartCount) by Name, ContainerName
| order by RestartCount desc

// CPU usage by container
Perf
| where ObjectName == "K8SContainer"
| where CounterName == "cpuUsageNanoCores"
| where InstanceName contains "airflow"
| summarize AvgCPU = avg(CounterValue) / 1000000000 by InstanceName
| order by AvgCPU desc

// Memory usage by container
Perf
| where ObjectName == "K8SContainer"
| where CounterName == "memoryRssBytes"
| where InstanceName contains "airflow"
| summarize AvgMemoryMB = avg(CounterValue) / 1048576 by InstanceName
| order by AvgMemoryMB desc

// Airflow task execution logs
ContainerLog
| where Namespace == "airflow"
| where LogEntry contains "azure_blob_copy"
| project TimeGenerated, ContainerName, LogEntry
| order by TimeGenerated desc
```

### 4. Create Alerts

**Path:** AKS Cluster → Alerts → New alert rule

**Recommended Alerts:**

1. **High CPU Usage**
   - Signal: Percentage CPU
   - Condition: Greater than 80%
   - Period: 5 minutes
   - Action: Email notification

2. **Pod Restarts**
   - Signal: Restart count
   - Condition: Greater than 3 in 15 minutes
   - Action: Teams notification

3. **Failed DAG Runs**
   - Use Log Query Alert
   - Query: Search for "failed" in scheduler logs
   - Threshold: More than 5 in 1 hour

4. **Memory Pressure**
   - Signal: Available memory percentage
   - Condition: Less than 10%
   - Period: 10 minutes

### 5. Create Custom Workbook

**Path:** AKS Cluster → Workbooks → New

Build custom dashboards with:
- DAG execution trends
- Success vs failure rates
- Resource utilization over time
- Cost analysis

---

## 🔔 Setting Up Alerts (Example)

### Email Alert for Failed Pods

```powershell
# Create action group for email notifications
az monitor action-group create \
  --resource-group bi_lakehouse_dev_rg \
  --name airflow-alerts \
  --short-name airflow \
  --email-receiver name="Team" email="your-team@example.com"

# Create alert rule for pod failures
az monitor metrics alert create \
  --resource-group bi_lakehouse_dev_rg \
  --name airflow-pod-failures \
  --scopes "/subscriptions/12f4f875-7d27-4234-889e-249988508376/resourcegroups/bi_lakehouse_dev_rg/providers/Microsoft.ContainerService/managedClusters/aks-airflow-poc" \
  --condition "avg Percentage CPU > 80" \
  --window-size 5m \
  --evaluation-frequency 1m \
  --action airflow-alerts
```

---

## 💰 Cost Management

**Current Configuration:**
- Log Analytics: Pay-as-you-go (Per GB ingested)
- Retention: 30 days included
- Estimated Cost: $5-15/month for this cluster size

**Cost Optimization:**
- Reduce retention period: `az monitor log-analytics workspace update --retention-time 7`
- Set daily cap: Portal → Log Analytics → Usage and estimated costs → Daily cap
- Filter unnecessary logs: Configure log collection settings

---

---

## 🎯 Alternative: HTML Dashboard (Still Available!)

While Azure Monitor provides enterprise-grade monitoring, the HTML dashboard is still useful for:
- Quick real-time checks
- Sharing with non-Azure users
- Offline viewing (via port-forward)

**Dashboard Location:**
```
C:\Users\sjogu\OneDrive - Spencer Gifts LLC\Documents\Srikanth_Jogu\Airflow_POC\monitoring\azure-monitor-alternative.html
```

**Access:**
```powershell
Start-Process "C:\Users\sjogu\OneDrive - Spencer Gifts LLC\Documents\Srikanth_Jogu\Airflow_POC\monitoring\azure-monitor-alternative.html"
```

---

## 📝 Summary

---

## 📝 Summary

✅ **Azure Monitor Container Insights:** Enabled and running  
✅ **Log Analytics Workspace:** `airflow-logs-workspace` (East US)  
✅ **Monitoring Agents:** Deployed (ama-logs daemonset)  
✅ **Data Collection:** Active (5-10 min initial delay)  

**You now have:**
1. Real-time cluster health monitoring
2. Historical performance data (30 days)
3. Advanced log querying with KQL
4. Alert capabilities for proactive monitoring
5. Cost tracking and analysis

**Next Steps:**
1. Wait 5-10 minutes for initial data collection
2. Access Azure Portal → `aks-airflow-poc` → Insights
3. Explore logs with the KQL queries above
4. Set up alerts for critical events
5. Create custom workbooks for your team

---

## 🆘 Troubleshooting

### No data appearing after 10 minutes?

```powershell
# Check if monitoring agents are running
kubectl get pods -n kube-system | Select-String "ama-logs"

# Should show 2/2 READY

# View agent logs
kubectl logs -n kube-system -l rsName=ama-logs --tail=50
```

### Want to disable monitoring?

```powershell
az aks disable-addons \
  --resource-group bi_lakehouse_dev_rg \
  --name aks-airflow-poc \
  --addons monitoring
```

### Change retention period?

```powershell
# Increase to 90 days
az monitor log-analytics workspace update \
  --resource-group bi_lakehouse_dev_rg \
  --workspace-name airflow-logs-workspace \
  --retention-time 90
```

---

**Last Updated:** December 4, 2025  
**Status:** ✅ Operational
