# 📦 Helm Migration Guide

Ready to level up? This guide helps you migrate from raw Kubernetes manifests to the official Apache Airflow Helm chart. 🚀

> **🎯 Why Helm?** Easier upgrades, built-in best practices, and unified configuration management!

## 💡 Why Migrate
- Easier upgrades and configuration management
- Built-in best practices and templating
- Unified deployment via Helm

## Current Parity
The file `kubernetes/helm-values.yaml` mirrors your raw manifests:
- External PostgreSQL (`postgres` service in `airflow` namespace)
- Redis enabled; `CeleryExecutor`
- Airflow image `apache/airflow:2.9.3` with `IfNotPresent`
- Admin user bootstrap
- Non-root `airflowUser: 50000`
- Resource requests/limits set
- Flower disabled

## Prerequisites
- Docker Desktop with Kubernetes
- `kubectl` installed
- Helm installed

## Install via Helm
```powershell
kubectl create namespace airflow
helm repo add apache-airflow https://airflow.apache.org
helm repo update
helm install airflow apache-airflow/airflow -n airflow -f kubernetes/helm-values.yaml
```

## Access Web UI
```powershell
kubectl port-forward svc/airflow-webserver 8080:8080 -n airflow
# If busy:
kubectl port-forward svc/airflow-webserver 9090:8080 -n airflow
# Open http://localhost:8080 or http://localhost:9090
```

## Production Considerations
- Replace plaintext DB credentials with an existing Kubernetes Secret
- Enable persistence for DAGs and logs
- Add Ingress for stable access
- Configure monitoring (Prometheus/Grafana)
- Set NetworkPolicies
- Back up PostgreSQL regularly

## Rolling Back
To uninstall Helm release:
```powershell
helm uninstall airflow -n airflow
```
Then re-apply raw manifests:
```powershell
kubectl apply -f kubernetes/postgres.yaml
kubectl apply -f kubernetes/airflow.yaml
```

## Troubleshooting
- Check pods: `kubectl get pods -n airflow`
- View logs: `kubectl logs -f deployment/airflow-webserver -n airflow`
- Describe resources: `kubectl describe pod <pod> -n airflow`

## Next Steps
- Tune resources and concurrency for your workload
- Add Connections in Airflow UI (Admin → Connections)
- Run `enterprise_integration_dag` and validate
