# Centralized DAG Monitoring in Azure Monitor

## 🎯 Overview

This guide sets up a **comprehensive DAG monitoring dashboard** in Azure Monitor that provides:

✅ **Real-time DAG execution metrics**  
✅ **Success/failure trends**  
✅ **Performance analytics**  
✅ **Centralized alerting**  
✅ **Historical analysis (30 days)**

---

## 📊 Step 1: Deploy the Azure Monitor Workbook

### Option A: Via Azure Portal (Recommended)

1. **Open Azure Portal:** https://portal.azure.com

2. **Navigate to Azure Monitor:**
   - Search for "Monitor" in the top search bar
   - Click "Azure Monitor"

3. **Create Workbook:**
   - Click "Workbooks" in the left menu
   - Click "+ New"
   - Click "</> Advanced Editor" (top toolbar)

4. **Import Workbook:**
   - Copy the entire contents of: `monitoring/azure-dag-monitoring-workbook.json`
   - Paste into the editor (replace existing JSON)
   - Click "Apply"

5. **Configure Workspace:**
   - Click "Resource" dropdown at the top
   - Select: `airflow-logs-workspace`
   - Resource Group: `bi_lakehouse_dev_rg`

6. **Save Workbook:**
   - Click "Save" icon (disk icon in toolbar)
   - Title: `Airflow DAG Monitoring`
   - Location: `bi_lakehouse_dev_rg`
   - Click "Save"

7. **Pin to Dashboard:**
   - Click "Pin" icon
   - Select "Create new" dashboard
   - Name: `Airflow Operations`
   - Click "Pin"

### Option B: Via Azure CLI

```powershell
# Create workbook from JSON file
$workbookContent = Get-Content "monitoring/azure-dag-monitoring-workbook.json" -Raw

az resource create `
  --resource-group bi_lakehouse_dev_rg `
  --resource-type "Microsoft.Insights/workbooks" `
  --name "airflow-dag-monitoring" `
  --properties "$workbookContent"
```

---

## 📈 Step 2: What You'll See in the Dashboard

### Panel 1: DAG Execution Overview (Tiles)
- **Total Executions:** Count of all DAG runs
- **Success Count:** Successfully completed runs
- **Failure Count:** Failed runs
- **Queued Count:** Tasks waiting to execute
- **Success Rate:** Percentage of successful runs

### Panel 2: DAG Runs by Status (Pie Chart)
- Visual breakdown of Success/Failed/Running/Queued states
- Click slices to filter other panels

### Panel 3: DAG Execution Trend (Time Chart)
- Success vs Failed runs over time
- Identify patterns and spikes
- Adjustable time range (1h to 30 days)

### Panel 4: Recent Failed DAG Runs (Table)
- Last 50 failures with timestamps
- DAG name and task name extracted
- Click log entries to see full details
- Filterable and sortable

### Panel 5: Top DAGs by Execution Count (Table)
- Most frequently running DAGs
- Success rate percentage
- Color-coded success rates (green=good, red=bad)

### Panel 6: DAG Execution Duration (Table)
- Average, Max, Min execution times
- Identify slow-running DAGs
- Execution count per DAG

### Panel 7: Tasks with Most Retries (Table)
- Tasks that fail and retry frequently
- Helps identify problematic tasks
- Sorted by retry count

### Panel 8: Airflow Pod Resource Usage (Chart)
- CPU and memory trends
- Correlate resource spikes with DAG runs
- Identify resource bottlenecks

### Panel 9: Top 10 Most Active DAGs (Bar Chart)
- Visual representation of DAG activity
- Quick identification of busiest DAGs

---

## 🔔 Step 3: Set Up Automated Alerts

### Alert 1: DAG Failure Alert

```powershell
# Create action group for notifications (if not already created)
az monitor action-group create `
  --resource-group bi_lakehouse_dev_rg `
  --name airflow-dag-alerts `
  --short-name dagalert `
  --email-receiver name="Team" email="your-team@example.com"

# Create scheduled query alert for DAG failures
az monitor scheduled-query create `
  --resource-group bi_lakehouse_dev_rg `
  --name "DAG Failure Alert" `
  --scopes "/subscriptions/12f4f875-7d27-4234-889e-249988508376/resourceGroups/bi_lakehouse_dev_rg/providers/Microsoft.OperationalInsights/workspaces/airflow-logs-workspace" `
  --condition "count 'Placeholder' > 0" `
  --condition-query "ContainerLog | where Namespace == 'airflow' | where LogEntry contains 'failed' or LogEntry contains 'ERROR' | where LogEntry contains 'DAG' | where TimeGenerated > ago(5m) | summarize FailureCount = count()" `
  --description "Alert when any DAG fails" `
  --evaluation-frequency 5m `
  --window-size 5m `
  --severity 2 `
  --action-groups "/subscriptions/12f4f875-7d27-4234-889e-249988508376/resourceGroups/bi_lakehouse_dev_rg/providers/Microsoft.Insights/actionGroups/airflow-dag-alerts"
```

### Alert 2: Long-Running DAG Alert

**Create via Portal:**
1. Go to: Azure Monitor → Alerts → Create alert rule
2. **Scope:** Select `airflow-logs-workspace`
3. **Condition:** Custom log search
4. **Query:**
   ```kusto
   ContainerLog
   | where Namespace == "airflow"
   | where LogEntry contains "Running for"
   | extend Duration = extract(@"Running for (\d+\.?\d*) seconds", 1, LogEntry)
   | where todouble(Duration) > 3600  // Alert if running > 1 hour
   | summarize Count = count()
   ```
5. **Alert logic:** When Count is greater than 0
6. **Evaluation:** Every 15 minutes, period 15 minutes
7. **Actions:** Select `airflow-dag-alerts`
8. **Alert details:** Name: "Long Running DAG Alert", Severity: Warning

### Alert 3: High DAG Failure Rate

**Query:**
```kusto
ContainerLog
| where Namespace == "airflow"
| where TimeGenerated > ago(1h)
| extend Status = case(
    LogEntry contains "success", "Success",
    LogEntry contains "failed", "Failed",
    "Other"
)
| where Status in ("Success", "Failed")
| summarize SuccessCount = countif(Status == "Success"), FailureCount = countif(Status == "Failed")
| extend FailureRate = (todouble(FailureCount) / (SuccessCount + FailureCount)) * 100
| where FailureRate > 20  // Alert if >20% failures
```

**Alert when:** FailureRate > 20  
**Frequency:** Every 30 minutes

---

## 📱 Step 4: Access Your Dashboard

### Web Portal
1. Go to: https://portal.azure.com
2. Search: "Monitor"
3. Click: "Workbooks"
4. Select: "Airflow DAG Monitoring"

### Direct Link
After saving, you'll get a URL like:
```
https://portal.azure.com/#blade/Microsoft_Azure_Monitoring/WorkbooksExtension.ReactView/id/%2Fsubscriptions%2F12f4f875-7d27-4234-889e-249988508376%2FresourceGroups%2Fbi_lakehouse_dev_rg%2Fproviders%2FMicrosoft.Insights%2Fworkbooks%2Fairflow-dag-monitoring
```

**Bookmark this URL for quick access!**

### Azure Mobile App
- Download: "Azure mobile app" (iOS/Android)
- Login with your credentials
- Navigate to: Dashboards → Airflow Operations
- Get push notifications for alerts

---

## 🔍 Step 5: Custom Queries for Specific DAGs

### Monitor Your azure_blob_copy DAG

```kusto
ContainerLog
| where Namespace == "airflow"
| where LogEntry contains "azure_blob_copy"
| where TimeGenerated > ago(7d)
| extend Status = case(
    LogEntry contains "Success" or LogEntry contains "copied", "Success",
    LogEntry contains "failed" or LogEntry contains "Error", "Failed",
    LogEntry contains "Starting", "Running",
    "Unknown"
)
| summarize Count = count() by Status, bin(TimeGenerated, 1h)
| render timechart
```

### Get DAG Execution History

```kusto
ContainerLog
| where Namespace == "airflow"
| where LogEntry contains "azure_blob_copy"
| where TimeGenerated > ago(30d)
| extend ExecutionDate = format_datetime(TimeGenerated, 'yyyy-MM-dd HH:mm:ss')
| project ExecutionDate, LogEntry
| order by ExecutionDate desc
```

### Find Files Copied by azure_blob_copy

```kusto
ContainerLog
| where Namespace == "airflow"
| where LogEntry contains "azure_blob_copy"
| where LogEntry contains "Copying:" or LogEntry contains "Copied:"
| extend FileName = extract(@"Copying: ([^\s]+)", 1, LogEntry)
| where isnotempty(FileName)
| project TimeGenerated, FileName, LogEntry
| order by TimeGenerated desc
```

---

## 📊 Step 6: Create Custom Alerts for Your DAGs

### Alert When azure_blob_copy Fails

```powershell
az monitor scheduled-query create `
  --resource-group bi_lakehouse_dev_rg `
  --name "azure_blob_copy Failure" `
  --scopes "/subscriptions/12f4f875-7d27-4234-889e-249988508376/resourceGroups/bi_lakehouse_dev_rg/providers/Microsoft.OperationalInsights/workspaces/airflow-logs-workspace" `
  --condition "count 'Placeholder' > 0" `
  --condition-query "ContainerLog | where Namespace == 'airflow' | where LogEntry contains 'azure_blob_copy' | where LogEntry contains 'failed' or LogEntry contains 'Error' | where TimeGenerated > ago(5m) | summarize Count = count()" `
  --description "Alert when azure_blob_copy DAG fails" `
  --evaluation-frequency 5m `
  --window-size 5m `
  --severity 2 `
  --action-groups "/subscriptions/12f4f875-7d27-4234-889e-249988508376/resourceGroups/bi_lakehouse_dev_rg/providers/Microsoft.Insights/actionGroups/airflow-dag-alerts"
```

### Alert When No Files Copied

```kusto
ContainerLog
| where Namespace == "airflow"
| where LogEntry contains "azure_blob_copy"
| where LogEntry contains "Found 0 files" or LogEntry contains "No files found"
| where TimeGenerated > ago(5m)
| summarize Count = count()
```

**Set alert:** When Count > 0

---

## 🎯 Step 7: Share Dashboard with Team

### Option 1: Share Workbook Link
1. Open your workbook
2. Click "Share" icon (top toolbar)
3. Copy link
4. Share with team members
5. They need "Reader" access to resource group

### Option 2: Export to PDF
1. Open workbook
2. Click "..." (more options)
3. Select "Print"
4. Choose "Save as PDF"
5. Email to stakeholders

### Option 3: Pin to Shared Dashboard
1. Create shared dashboard: Portal → Dashboards → New Dashboard
2. Open your workbook
3. Click "Pin" icon on any panel
4. Select the shared dashboard
5. All team members with access can view

---

## 💡 Best Practices

### 1. Regular Monitoring Schedule
- **Daily:** Check failure counts and recent errors
- **Weekly:** Review execution duration trends
- **Monthly:** Analyze retry patterns and optimize DAGs

### 2. Alert Tuning
- Start with broad alerts (any failure)
- Refine after understanding normal patterns
- Avoid alert fatigue (too many notifications)

### 3. Dashboard Customization
- Add panels for your specific DAGs
- Create separate workbooks for different teams
- Use parameters to filter by environment (dev/prod)

### 4. Data Retention
- Current: 30 days retention
- Extend if needed:
  ```powershell
  az monitor log-analytics workspace update `
    --resource-group bi_lakehouse_dev_rg `
    --workspace-name airflow-logs-workspace `
    --retention-time 90
  ```

### 5. Cost Management
- Monitor ingestion costs: Portal → Log Analytics → Usage and estimated costs
- Set daily cap if needed
- Archive old data to cheaper storage

---

## 🆘 Troubleshooting

### Dashboard Shows No Data

**Check:**
1. Wait 5-10 minutes after initial setup (data collection lag)
2. Verify monitoring agents running:
   ```powershell
   kubectl get pods -n kube-system | Select-String "ama-logs"
   ```
3. Check if logs are flowing:
   ```powershell
   kubectl logs -n kube-system -l rsName=ama-logs --tail=50
   ```

### Alerts Not Triggering

**Check:**
1. Verify action group has correct email/phone
2. Test action group: Portal → Action Groups → Test
3. Check alert rule is enabled
4. Review alert history: Portal → Alerts → Alert Rules → [Your Rule] → History

### Query Returns No Results

**Try:**
1. Expand time range (top parameter)
2. Verify DAG name spelling in query
3. Check if DAG has actually run in the time period
4. Test simpler query first:
   ```kusto
   ContainerLog
   | where Namespace == "airflow"
   | take 10
   ```

---

## 📚 Additional Resources

### Official Documentation
- [Azure Monitor Workbooks](https://learn.microsoft.com/en-us/azure/azure-monitor/visualize/workbooks-overview)
- [KQL Query Language](https://learn.microsoft.com/en-us/azure/data-explorer/kusto/query/)
- [Log Analytics Alerts](https://learn.microsoft.com/en-us/azure/azure-monitor/alerts/alerts-types)

### Sample Queries Library
- Saved in workbook for reuse
- Browse: Portal → Log Analytics → Queries → "Airflow" tag
- Community: https://github.com/Azure/azure-quickstart-templates

---

## ✅ Quick Start Checklist

- [ ] Import workbook to Azure Monitor
- [ ] Configure Log Analytics workspace
- [ ] Save and pin to dashboard
- [ ] Create action group for notifications
- [ ] Set up DAG failure alert
- [ ] Test alert by triggering a failure
- [ ] Share dashboard link with team
- [ ] Bookmark direct URL
- [ ] Schedule weekly review meeting

---

## 🎉 Summary

You now have:
- ✅ **Centralized dashboard** for all DAG monitoring
- ✅ **Real-time visibility** into executions, failures, performance
- ✅ **Automated alerts** for critical events
- ✅ **Historical analysis** with 30-day retention
- ✅ **Shareable** with entire team
- ✅ **Mobile access** via Azure app

**Access:** https://portal.azure.com → Monitor → Workbooks → Airflow DAG Monitoring

---

**Last Updated:** December 4, 2025  
**Status:** ✅ Ready to Deploy  
**Estimated Setup Time:** 15 minutes
