# Grafana Setup Guide for Airflow Monitoring

## 🎉 Grafana is Deployed and Ready!

**Access Information:**
- **URL:** http://20.75.172.198
- **Username:** `admin`
- **Password:** `NewPassword123`

**Deployed:** December 4, 2025  
**Version:** Grafana 10.3.0  
**Namespace:** default  
**External IP:** 20.75.172.198

---

## Step 1: Access Grafana
1. Open your browser
2. Go to: `http://localhost:3000` (if using port-forward)
3. Login with:
   - Username: `admin`
   - Password: `NewPassword123`

---

## Step 2: Add Prometheus Data Source

1. Click the **gear icon (⚙️)** on the left sidebar
2. Click **Data Sources**
3. Click **Add data source** (blue button)
4. Click **Prometheus** from the list
5. In the **URL** field, enter: `http://localhost:9090`
6. Scroll down and click **Save & Test**
7. You should see: "Successfully queried the Prometheus API" (green message)

---

## Step 3: Import Simple Dashboard

1. Click the **plus icon (+)** on the left sidebar
2. Click **Import dashboard**
3. Click **Upload JSON file**
4. Navigate to: `monitoring/simple-airflow-dashboard.json`
5. Select the file and click **Open**
6. On the import page:
   - You'll see "Simple Airflow Monitoring" dashboard
   - Under **Data Source**, select **Prometheus** from the dropdown
7. Click **Import**

---

## Step 4: View Your Dashboard

You should now see a dashboard with 3 panels:
1. **Prometheus Up Status** - Shows which services are up
2. **Total Services Up** - Gauge showing count of services
3. **CPU Usage by Service** - CPU usage over time

These are simple panels that work with any Prometheus data. If you see data in these panels, your connection is working!

---

## Step 5: Verify Data is Showing

- If you see graphs with data → Success! Your monitoring is working.
- If you see "No data":
  - Check that port-forward is still running
  - Try changing the time range (top right) to "Last 6 hours" or "Last 24 hours"
  - Click the refresh icon

---

## Step 6: Add Airflow-Specific Panels (After Airflow Metrics are Available)

Once Airflow starts exporting metrics, you can add panels for:
- DAG success rates
- Task failures
- Queue sizes
- Execution times

---

## Troubleshooting

### Problem: "No data" in all panels
**Solution:**
- Ensure port-forward is running:
  ```powershell
  kubectl port-forward svc/prometheus-server 9090:80 -n default
  ```
- Check Prometheus is accessible: Open `http://localhost:9090` in browser

### Problem: Cannot import dashboard
**Solution:**
- Make sure you selected the correct JSON file
- Ensure Prometheus data source is created first
- Try the `simple-airflow-dashboard.json` file instead

### Problem: Dashboard imported but shows errors
**Solution:**
- Edit the dashboard settings (gear icon at top)
- Under General, set Data Source to Prometheus
- Save the dashboard

---

## Next Steps

Once you have the basic dashboard working:
1. Configure Airflow to export metrics to Prometheus
2. Add more panels for Airflow-specific metrics
3. Set up alerts for failures
4. Create dashboards for each service (Azure, Databricks, etc.)

---

## Quick Commands Reference

**Port-forward Grafana:**
```powershell
kubectl port-forward svc/grafana 3000:80 -n default
```

**Port-forward Prometheus:**
```powershell
kubectl port-forward svc/prometheus-server 9090:80 -n default
```

**Check services:**
```powershell
kubectl get svc -n default
kubectl get pods -n default
```

---

## Support

If you need help at any step, provide:
1. Screenshot of the error
2. Which step you're on
3. Output of `kubectl get svc -n default`
