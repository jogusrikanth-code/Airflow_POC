# Azure Monitor Permission Request

## Request Summary
I need permissions to enable Azure Monitor Container Insights on the AKS cluster for monitoring our Airflow deployment.

## Required Permissions

Please grant one of the following RBAC roles on Resource Group: `bi_lakehouse_dev_rg`

### Option 1: Contributor Role (Recommended)
```
Role: Contributor
Scope: /subscriptions/<subscription-id>/resourceGroups/bi_lakehouse_dev_rg
```

### Option 2: Specific Monitoring Roles
If Contributor is too broad, grant these specific roles:
- `Monitoring Contributor`
- `Log Analytics Contributor`
- `Monitoring Metrics Publisher`

## What This Enables

Once permissions are granted, I can enable:

✅ **Container Insights**
- Real-time pod and container metrics
- CPU, memory, disk, network monitoring
- Container logs aggregation

✅ **Log Analytics Workspace**
- Historical data retention (90 days default)
- KQL query capabilities
- Custom workbooks and dashboards

✅ **Alerting**
- Automated alerts for:
  - High CPU/memory usage
  - Pod failures
  - DAG execution failures
  - Disk space warnings

✅ **Integration**
- Azure DevOps integration
- Teams/Email notifications
- Logic Apps workflows

## Business Justification

**Problem:** Currently limited to real-time monitoring only (HTML dashboard)

**Solution:** Azure Monitor provides:
1. Historical trend analysis (identify patterns)
2. Proactive alerting (prevent downtime)
3. Better troubleshooting (query logs)
4. Compliance (audit trail)

**Cost:** ~$5-15/month for Log Analytics (minimal)

## Command to Enable (After Approval)

```powershell
az aks enable-addons \
  --resource-group bi_lakehouse_dev_rg \
  --name aks-airflow-poc \
  --addons monitoring
```

## Current Workaround

Until permissions are granted, I'm using:
- HTML dashboard for real-time monitoring
- kubectl commands for log access
- Manual tracking of metrics

## Contact

**Requester:** Srikanth Jogu  
**Date:** December 4, 2025  
**Cluster:** aks-airflow-poc  
**Resource Group:** bi_lakehouse_dev_rg
