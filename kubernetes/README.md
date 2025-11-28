# Kubernetes Deployment Guide

This directory contains modern Kubernetes manifests for deploying Apache Airflow 2.9.3 on Kubernetes.

## Files Overview

- `postgres.yaml` - PostgreSQL database deployment with PersistentVolume
- `airflow.yaml` - Airflow components (Webserver, Scheduler, Worker, Redis)
- `values.yaml` - Helm chart reference values for future migrations

## Architecture

```
┌─────────────────────────────────────────┐
│      Kubernetes Cluster (Docker         │
│         Desktop / Docker K8s)           │
├─────────────────────────────────────────┤
│                                         │
│  Airflow Namespace                      │
│  ├─ airflow-webserver (1 pod)          │
│  ├─ airflow-scheduler (1 pod)          │
│  ├─ airflow-worker (1 pod)             │
│  ├─ redis (1 pod)                      │
│  └─ postgres (1 pod + PVC)             │
│                                         │
│  DAGs Volume (HostPath)                │
│  └─ /opt/airflow/dags                  │
│                                         │
│  Logs Volume (EmptyDir)                │
│  └─ /opt/airflow/logs                  │
│                                         │
└─────────────────────────────────────────┘
```

## Deployment Instructions

### Prerequisites

- Docker Desktop with Kubernetes enabled
- `kubectl` CLI (comes with Docker Desktop)
- Helm installed (optional, for future upgrades)

### Step 1: Deploy PostgreSQL

```powershell
kubectl apply -f kubernetes/postgres.yaml
kubectl wait --for=condition=ready pod -l app=postgres -n airflow --timeout=300s
```

### Step 2: Deploy Airflow

```powershell
kubectl apply -f kubernetes/airflow.yaml
kubectl get pods -n airflow
```

### Step 3: Access Airflow UI

Port-forward to the webserver (try 8080, fallback 9090):

```powershell
kubectl port-forward svc/airflow-webserver 8080:8080 -n airflow
kubectl port-forward svc/airflow-webserver 9090:8080 -n airflow
```

**Default Credentials:**
- Username: `admin`
- Password: `admin`

## Useful Commands

### View Pods

```powershell
kubectl get pods -n airflow
kubectl describe pod <pod-name> -n airflow
```

### View Logs

```powershell
# Webserver logs
kubectl logs -f deployment/airflow-webserver -n airflow

# Scheduler logs
kubectl logs -f statefulset/airflow-scheduler -n airflow

# Worker logs
kubectl logs -f statefulset/airflow-worker -n airflow

# PostgreSQL logs
kubectl logs -f deployment/postgres -n airflow
```

### Check Services

```powershell
kubectl get svc -n airflow
```

### Delete Everything

```powershell
kubectl delete namespace airflow
```

## Configuration

All configuration is managed via:
- **ConfigMap**: `airflow-config` - Airflow settings
- **Secret**: `airflow-secrets` - Sensitive data (DB connections)

To update configuration:

```powershell
kubectl edit configmap airflow-config -n airflow
kubectl edit secret airflow-secrets -n airflow
```

### Resource Requests and Limits

Modify in `airflow.yaml` for each component:

```yaml
resources:
  requests:
    memory: "512Mi"
    cpu: "500m"
  limits:
    memory: "1024Mi"
    cpu: "1000m"
```

### Scaling Workers

To scale Celery workers:

```powershell
kubectl scale statefulset/airflow-worker -n airflow --replicas=3
```

## Best Practices Used

✅ **Security Context** - Runs as non-root user (50000)
✅ **Health Checks** - Liveness and readiness probes on all components
✅ **Resource Management** - CPU/memory requests and limits set
✅ **StatefulSets** - Scheduler and workers use StatefulSets for stable identity
✅ **Init Containers** - Airflow DB upgrade runs before webserver starts
✅ **ConfigMaps & Secrets** - Separate configuration from code
✅ **RBAC** - ServiceAccount with minimal required permissions
✅ **Volume Management** - Proper mounts for DAGs, logs, plugins
✅ **Image Policy** - IfNotPresent to reduce Docker Hub rate limiting

## Troubleshooting

### Pods stuck in Init:0/1

Check init container logs:
```powershell
kubectl logs <pod-name> -c airflow-init -n airflow
```

### PostgreSQL connection errors

Verify PostgreSQL is running:
```powershell
kubectl get svc postgres -n airflow
kubectl exec -it <postgres-pod> -n airflow -- psql -U airflow -d airflow -c "SELECT 1"
```

### Redis connection errors

Verify Redis is running:
```powershell
kubectl get svc redis -n airflow
kubectl exec -it <redis-pod> -n airflow -- redis-cli ping
```

### Out of memory errors

Increase resource limits in `airflow.yaml` and redeploy:
```powershell
kubectl delete deployment airflow-webserver -n airflow
kubectl apply -f kubernetes/airflow.yaml
```

## Migration to Helm (Future)

To deploy using Helm chart instead (using `kubernetes/helm-values.yaml`):

```powershell
helm repo add apache-airflow https://airflow.apache.org
helm repo update

helm install airflow apache-airflow/airflow -f kubernetes/helm-values.yaml --namespace airflow
```

Notes:
- `kubernetes/helm-values.yaml` is aligned with the raw manifests (CeleryExecutor, external Postgres `postgres`, Redis enabled, non-root user).
- For production, replace plaintext DB credentials with an existing Kubernetes Secret and enable persistence for DAGs/logs.

## Production Considerations

For production deployments, consider:

1. **Persistent Logs** - Use PersistentVolume instead of EmptyDir
2. **High Availability** - Run multiple scheduler and worker replicas
3. **Ingress** - Use Ingress controller instead of LoadBalancer
4. **External Secrets** - Use secrets management system (Vault, AWS Secrets Manager)
5. **Monitoring** - Add Prometheus and Grafana for metrics
6. **Backup** - Backup PostgreSQL data regularly
7. **Network Policies** - Implement NetworkPolicies for security

- [Apache Airflow Kubernetes Docs](https://airflow.apache.org/docs/apache-airflow/stable/kubernetes.html)
- [Airflow Helm Chart](https://airflow.apache.org/docs/helm-chart/stable/index.html)
- [Kubernetes Best Practices](https://kubernetes.io/docs/concepts/configuration/overview/)
