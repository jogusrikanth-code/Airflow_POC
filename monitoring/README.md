# Airflow Monitoring

For this POC deployment on AKS, monitoring is handled through:

## Built-in Airflow UI

Access the Airflow Web UI for:
- DAG status and execution history
- Task logs and details
- Connection configuration
- Variable management
- XCom inspection

```powershell
# Port-forward to access UI
kubectl port-forward -n airflow svc/airflow-webserver 8080:8080
# Access at http://localhost:8080
```

## Pod and Container Logs

```powershell
# Scheduler logs
kubectl logs -n airflow deployment/airflow-scheduler -f

# Worker logs
kubectl logs -n airflow deployment/airflow-worker -f

# Webserver logs
kubectl logs -n airflow deployment/airflow-webserver -f

# All pods
kubectl logs -n airflow -l app.kubernetes.io/instance=airflow -f
```

## Kubernetes Dashboard

```powershell
# View pod status and events
kubectl get pods -n airflow -o wide
kubectl describe pod -n airflow <pod-name>
kubectl get events -n airflow
```

## Future Enhancements

For production monitoring, consider adding:
- **Prometheus** - Metrics collection from StatsD exporter
- **Grafana** - Dashboards for Airflow metrics
- **AlertManager** - Alert routing for critical events
- **Azure Monitor** - Integration with Azure Monitor for centralized logging
- **Slack Alerts** - Notifications for DAG failures

## Testing Monitoring

To verify all services are responding:

```powershell
# Check service endpoints
kubectl get svc -n airflow

# Test connectivity to services
kubectl run -it --rm debug --image=curlimages/curl --restart=Never -n airflow -- sh
# Inside pod:
# curl http://airflow-webserver:8080
# curl http://redis:6379
```
