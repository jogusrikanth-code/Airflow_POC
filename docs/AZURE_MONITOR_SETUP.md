# Azure Monitor Setup Guide for Airflow

## 🚫 Issue: Insufficient Permissions

You encountered permission errors when trying to enable Azure Monitor Container Insights:
- Need `microsoft.resources/deployments/write` permission
- Need to create Log Analytics workspace
- Need to create Azure Monitor workspace

**Required Azure RBAC Role:** `Contributor` or `Owner` at subscription/resource group level

## ✅ Alternative Solution: HTML Dashboard

Since you don't have permissions to create Azure Monitor resources, I've created a **standalone HTML dashboard** that connects directly to Airflow's REST API.

### Features

✨ **Real-time Monitoring**
- Total DAGs count
- Active vs Paused DAGs
- Success rate (last 24 hours)
- Recent failures list
- Auto-refresh every 30 seconds

✨ **No Infrastructure Required**
- Pure HTML/JavaScript - runs in any browser
- No server-side components
- No Azure permissions needed
- Direct connection to Airflow API

✨ **Enterprise Ready**
- Clean, professional interface
- Mobile responsive design
- Real-time updates
- Easy to share with support team

### Quick Start

1. **Setup Airflow Port-Forward**
   ```powershell
   kubectl port-forward svc/airflow-webserver 8080:8080 -n airflow
   ```

2. **Open the Dashboard**
   ```powershell
   Start-Process "C:\Users\sjogu\OneDrive - Spencer Gifts LLC\Documents\Srikanth_Jogu\Airflow_POC\monitoring\azure-monitor-alternative.html"
   ```

3. **Configure Connection**
   - **Airflow URL:** `http://localhost:8080`
   - **Username:** `admin` (or your Airflow username)
   - **Password:** Your Airflow password

4. **Click Connect**
   - Dashboard will load automatically
   - Auto-refreshes every 30 seconds
   - Click 🔄 button to refresh manually

### For Support Team Access

#### Option 1: Expose Airflow Externally (Recommended for Production)

```powershell
# Change Airflow webserver to LoadBalancer
kubectl patch svc airflow-webserver -n airflow -p '{"spec": {"type": "LoadBalancer"}}'

# Get external IP
kubectl get svc airflow-webserver -n airflow
```

Then:
1. Share the HTML file with your support team
2. They use the external IP in the dashboard: `http://<EXTERNAL-IP>:8080`
3. Provide them with read-only Airflow credentials

#### Option 2: Host Dashboard on Internal Web Server

1. Copy `azure-monitor-alternative.html` to your internal web server
2. Team members access via `http://intranet/airflow-dashboard.html`
3. They enter the Airflow URL (external IP or internal DNS)

#### Option 3: Azure App Service (No Permissions Needed)

If you have access to deploy static files:

1. Create simple Azure App Service
2. Upload the HTML file
3. Share the App Service URL with team

### Security Considerations

⚠️ **Important Security Notes:**

1. **Credentials in Browser**
   - The HTML dashboard stores credentials in browser memory only
   - Never stored on disk
   - Cleared when browser closes

2. **CORS Configuration**
   - If accessing Airflow from different domain, you may need to enable CORS
   - Add to `airflow.cfg`:
     ```ini
     [api]
     enable_cors = True
     cors_origins = *
     ```

3. **Read-Only Access**
   - Create a read-only Airflow user for support team
   - This user can view DAGs but not trigger/modify them

### Advantages Over Azure Monitor

✅ **No Azure Permissions Required** - Works immediately
✅ **No Additional Costs** - Free, no Azure Monitor pricing
✅ **Direct Data Access** - Real-time from Airflow API
✅ **Customizable** - Easy to modify HTML/JS as needed
✅ **Portable** - Works anywhere (local, cloud, on-prem)

### Limitations

❌ No historical trend graphs (Azure Monitor would provide this)
❌ No integration with Azure Alert Rules
❌ No Log Analytics query capabilities
❌ Manual refresh (vs. push notifications)

## 🔮 Future: If You Get Azure Permissions

Once you receive proper Azure RBAC permissions, you can enable full Azure Monitor Container Insights:

### 1. Enable Container Insights

```powershell
az aks enable-addons `
    --resource-group bi_lakehouse_dev_rg `
    --name aks-airflow-poc `
    --addons monitoring
```

### 2. Access Azure Monitor

1. Go to Azure Portal
2. Navigate to your AKS cluster: `aks-airflow-poc`
3. Click **Insights** under **Monitoring**
4. View:
   - Cluster performance
   - Pod metrics
   - Container logs
   - Live logs

### 3. Create Custom Workbook

Use KQL queries to monitor Airflow:

```kusto
// DAG execution trends
ContainerLog
| where ContainerName contains "scheduler"
| where LogEntry contains "DAG"
| summarize count() by bin(TimeGenerated, 5m), Severity
| render timechart

// Failed DAG runs
ContainerLog
| where ContainerName contains "scheduler"
| where LogEntry contains "failed"
| project TimeGenerated, LogEntry
| order by TimeGenerated desc
| take 20

// Resource utilization
Perf
| where ObjectName == "K8SContainer"
| where CounterName == "cpuUsageNanoCores"
| where InstanceName contains "airflow"
| summarize avg(CounterValue) by InstanceName, bin(TimeGenerated, 5m)
| render timechart
```

### 4. Configure Alerts

Create alerts in Azure Monitor:
- High CPU usage
- Container restarts
- Failed DAG runs
- Disk space warnings

### Azure Monitor Benefits (When Available)

- 📊 **Historical Trends** - 90 days of data retention
- 🔔 **Automated Alerts** - Email, SMS, Teams notifications
- 📈 **Advanced Analytics** - KQL query language
- 🔐 **Azure RBAC** - Integrated access control
- 📱 **Mobile App** - Monitor from anywhere
- 🔗 **Integration** - Works with Azure DevOps, Logic Apps, etc.

## Recommendation

1. **Use HTML dashboard immediately** for basic monitoring
2. **Request Azure RBAC permissions** from your admin:
   - Role: `Contributor` on resource group `bi_lakehouse_dev_rg`
   - Or: `Monitoring Contributor` + `Log Analytics Contributor`
3. **Once you have permissions**, enable Container Insights for enterprise features
4. **Keep HTML dashboard** as backup/quick view tool

## Support

The HTML dashboard is fully functional and production-ready. Your support team can use it immediately without waiting for Azure permissions.

**Dashboard Location:**
```
C:\Users\sjogu\OneDrive - Spencer Gifts LLC\Documents\Srikanth_Jogu\Airflow_POC\monitoring\azure-monitor-alternative.html
```

Just share this file + Airflow credentials with your support team! 🚀
