# Kubernetes Cleanup Summary

## What Was Cleaned Up ✅

### Old Files Removed
- ❌ `k8s-postgres.yaml` - Old basic manifest
- ❌ `k8s-airflow.yaml` - Old basic manifest
- ❌ `postgres-deployment.yaml` - Redundant file

### New Modern Manifests Created
- ✅ `kubernetes/postgres.yaml` — Production-ready PostgreSQL (PVC, probes, security context)
- ✅ `kubernetes/airflow.yaml` — Airflow stack (webserver, scheduler, worker, Redis)
- ✅ `kubernetes/values.yaml` — Helm chart reference for future upgrades
- ✅ `kubernetes/README.md` — Complete deployment guide (Windows PowerShell commands)

## Key Improvements 🚀
### Best Practices Implemented
| Area | Old | New |
|---|---|---|
| Security Context | ❌ | ✅ Non-root user (50000) |
| Probes | Basic | ✅ Advanced with failureThreshold |
| StatefulSets | ❌ | ✅ For Scheduler & Workers |
| Init Containers | ❌ | ✅ DB upgrade + admin bootstrap |
| Image Pull Policy | ❌ | ✅ IfNotPresent to reduce pulls |
| Health Checks | Simple | ✅ Comprehensive liveness/readiness |

**Old Setup:**
- Basic deployments only
- No StatefulSets
- Mixed configuration approaches
- Minimal documentation

**New Setup:**
- Separation of concerns (postgres.yaml, airflow.yaml)
- StatefulSets for Scheduler and Workers
- ConfigMaps + Secrets for configuration
- Comprehensive documentation (README.md)
- Helm reference values for future upgrades
- Production-ready resource management

### Component Configuration

#### PostgreSQL
```
Image: postgres:15-alpine
Replicas: 1
Storage: 5Gi PVC
Resources: 256Mi req / 512Mi limit
Health Checks: Yes (livenessProbe + readinessProbe)
Security: Running as postgres user (999)
```

#### Airflow Webserver
```
Image: apache/airflow:2.9.3
Replicas: 1
Service: LoadBalancer on port 8080
Resources: 512Mi req / 1024Mi limit
Health Checks: Yes (HTTP /health endpoint)
Security: Running as airflow user (50000)
```

#### Airflow Scheduler
```
Type: StatefulSet (stable identity)
Image: apache/airflow:2.9.3
Replicas: 1
Resources: 512Mi req / 1024Mi limit
Health Checks: Yes (job check probe)
```

#### Airflow Worker
```
Type: StatefulSet (stable identity)
Image: apache/airflow:2.9.3
Replicas: 1 (scalable to N)
Executor: CeleryExecutor
Resources: 512Mi req / 1024Mi limit
Health Checks: Yes (job check probe)
```

#### Redis
```
Image: redis:7-alpine
Replicas: 1
No persistence (for POC)
Resources: 128Mi req / 256Mi limit
Health Checks: Yes (ping command)
```

## Deployment Instructions

### Quick Start (Windows PowerShell)

```powershell
# 1. Deploy PostgreSQL
kubectl apply -f "kubernetes/postgres.yaml"

# 2. Deploy Airflow
kubectl apply -f "kubernetes/airflow.yaml"

# 3. Access UI (try 8080, fallback 9090)
kubectl port-forward svc/airflow-webserver 8080:8080 -n airflow
# If 8080 is busy:
kubectl port-forward svc/airflow-webserver 9090:8080 -n airflow

# 4. Open browser
# http://localhost:8080  (or http://localhost:9090)
# Username: admin
# Password: admin
```

### Verify Deployment

```powershell
# Check pods
kubectl get pods -n airflow

# Check services
kubectl get svc -n airflow

# Check volumes
kubectl get pvc -n airflow
```

## Configuration Management

### ConfigMaps (airflow-config)
Contains non-sensitive Airflow settings:
- `AIRFLOW__CORE__DAGS_FOLDER`
- `AIRFLOW__CORE__EXECUTOR`
- `AIRFLOW__CELERY__WORKER_CONCURRENCY`
- etc.

### Secrets (airflow-secrets)
Contains sensitive data:
- `sql_alchemy_conn` - PostgreSQL connection
- `celery_broker_url` - Redis broker URL
- `celery_result_backend` - Celery result backend

### How to Update

```powershell
# Edit ConfigMap
kubectl edit configmap airflow-config -n airflow

# Edit Secret
kubectl edit secret airflow-secrets -n airflow
```

## Next Steps

1. **Deploy New Manifests**
   ```powershell
   # Caution: deleting the namespace removes all resources in it
   kubectl delete namespace airflow
   kubectl apply -f "kubernetes/postgres.yaml"
   kubectl apply -f "kubernetes/airflow.yaml"
   ```

2. **Verify All Pods Running**
   ```bash
   kubectl get pods -n airflow
   ```

3. **Test `enterprise_integration_dag`**
   - Access UI at http://localhost:8080 (or http://localhost:9090)
   - Enable the DAG
   - Trigger a test run
   - Monitor execution

4. **Check DAG Sync**
   ```powershell
   kubectl logs -f deployment/airflow-webserver -n airflow | Select-String "DAG"
   ```

## Production Readiness Checklist

- ✅ Security contexts configured
- ✅ Resource limits set
- ✅ Health checks implemented
- ✅ RBAC configured
- ✅ Logging configured
- ⏳ Monitoring (Prometheus/Grafana) - TODO
- ⏳ Backup strategy - TODO
- ⏳ Scaling policy - TODO
- ⏳ Network policies - TODO

## Troubleshooting

### Check Pod Status
```powershell
kubectl describe pod <pod-name> -n airflow
```

### View Logs
```powershell
kubectl logs <pod-name> -n airflow
```

### Restart a Component
```powershell
kubectl rollout restart deployment/airflow-webserver -n airflow
```

### Delete and Redeploy
```powershell
kubectl delete namespace airflow
kubectl apply -f "kubernetes/postgres.yaml"
kubectl apply -f "kubernetes/airflow.yaml"
```

## References

- [Airflow Kubernetes Documentation](https://airflow.apache.org/docs/apache-airflow/stable/kubernetes.html)
- [Airflow Helm Chart](https://airflow.apache.org/docs/helm-chart/stable/index.html)
- [Kubernetes Best Practices](https://kubernetes.io/docs/concepts/configuration/overview/)

---

**Status:** ✅ Repository cleaned up and modernized with production-ready Kubernetes manifests
