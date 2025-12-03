# 🏢 Enterprise-Grade Airflow on Kubernetes — Architecture & Implementation Guide

Planning a production deployment? This comprehensive guide covers reliability, scalability, security, and maintainability patterns for enterprise Airflow. 🚀

> **🎯 Audience:** Architects, Platform Engineers, Tech Leads planning large-scale production deployments

## 1️⃣ Overview & Architecture

Enterprise Airflow on Kubernetes is designed for reliability, scalability, security, and maintainability. It leverages Kubernetes features (HA, RBAC, PVC, Ingress, monitoring) and best practices for production.

### Core Components & Roles
- **Webserver**: UI & REST API for DAG management and monitoring.
- **Scheduler**: Orchestrates DAG runs, schedules tasks, and enqueues them.
- **Workers (Celery)**: Execute tasks in parallel, scale horizontally.
- **Flower**: Celery monitoring dashboard (optional).
- **Redis**: Celery broker for task queueing.
- **PostgreSQL**: Metadata DB (HA, backups, PVC).
- **DAGs/Plugins/Logs**: Mounted via PersistentVolume or object storage (S3/GCS).
- **Ingress Controller**: Securely exposes UI/API.
- **Monitoring**: Prometheus, Grafana, Alertmanager.
- **Secrets Management**: Vault, KMS, or Kubernetes Secrets.
- **Backup/Restore**: Automated for DB, DAGs, logs.
- **RBAC & Network Policies**: Security and traffic control.

### Enterprise Flow Diagram
```
┌─────────────────────────────────────────────────────────────┐
│                  Kubernetes Cluster (Production)            │
├─────────────────────────────────────────────────────────────┤
│ Namespace: airflow                                          │
│                                                             │
│ ┌─────────────┐   ┌─────────────┐   ┌─────────────┐         │
│ │ Webserver   │<--│ Ingress     │--►│ User/Admin  │         │
│ └─────▲───────┘   └─────────────┘   └─────────────┘         │
│       │                                                  │
│ ┌─────┴───────┐                                         │
│ │ Scheduler   │◄───────────────────────────────────────┐ │
│ └─────▲───────┘                                         │
│       │  Enqueue tasks                                  │
│ ┌─────┴───────┐                                         │
│ │ Redis      │◄───────────────────────────────────────┐ │
│ └─────▲───────┘                                         │
│       │  Workers pull tasks                             │
│ ┌─────┴───────┐                                         │
│ │ Workers    │◄───────────────────────────────────────┐ │
│ └─────────────┘                                         │
│                                                         │
│ ┌─────────────┐                                         │
│ │ Flower      │ (optional, monitor Celery)              │
│ └─────────────┘                                         │
│                                                         │
│ ┌─────────────┐                                         │
│ │ PostgreSQL  │ (HA, backups, PVC)                      │
│ └─────────────┘                                         │
│                                                         │
│ ┌─────────────┐                                         │
│ │ DAGs/Logs   │ (PVC, S3, GCS, etc.)                    │
│ └─────────────┘                                         │
│                                                         │
│ ┌─────────────┐                                         │
│ │ Monitoring  │ (Prometheus, Grafana)                   │
│ └─────────────┘                                         │
│                                                         │
│ ┌─────────────┐                                         │
│ │ Secrets     │ (Vault/KMS/K8s Secrets)                 │
│ └─────────────┘                                         │
│                                                         │
│ ┌─────────────┐                                         │
│ │ NetworkPolicy│ (restrict traffic)                     │
│ └─────────────┘                                         │
└─────────────────────────────────────────────────────────────┘
```

---

## 2. Step-by-Step Implementation Procedure

### Step 1: Prepare Kubernetes Cluster
- **Why:** Production needs HA, scaling, security.
- **What:** Use managed K8s (EKS, AKS, GKE) or hardened on-prem cluster. Confirm `kubectl` and Helm access.
- **Reason:** Ensures reliability, upgrades, and security.

### Step 2: Create Namespace & RBAC
- **Why:** Isolate Airflow, control permissions.
- **What:**
  - Create `airflow` namespace.
  - Create ServiceAccount, Roles, RoleBindings for Airflow pods.
- **Reason:** Prevents accidental cross-app access and enforces least privilege.

### Step 3: Provision Persistent Storage
- **Why:** DAGs, logs, and DB need durable storage.
- **What:**
  - Create PersistentVolumeClaims for DAGs, logs, and Postgres.
  - Use cloud storage (S3/GCS) for DAGs/logs if possible.
- **Reason:** Survives pod restarts and node failures.

### Step 4: Deploy PostgreSQL (Highly Available)
- **Why:** Metadata DB is critical; must be HA and backed up.
- **What:**
  - Use Helm chart or operator (Zalando, CrunchyData) with replication, backups, PVC.
  - Automate backups (pgBackRest, cloud snapshots).
- **Reason:** Prevents data loss and downtime.

### Step 5: Deploy Redis (Highly Available)
- **Why:** Celery broker must be reliable.
- **What:**
  - Use Redis Helm chart with replication/sentinel.
- **Reason:** Ensures task queue is always available.

### Step 6: Configure Secrets Management
- **Why:** Protect credentials and sensitive configs.
- **What:**
  - Use Vault, KMS, or Kubernetes Secrets.
  - Integrate with Airflow via environment variables or Helm values.
- **Reason:** Avoids hardcoding secrets in manifests.

### Step 7: Deploy Airflow via Helm Chart
- **Why:** Helm provides templating, upgrades, and best practices.
- **What:**
  - Use official Airflow Helm chart with custom `values.yaml`:
    - External Postgres/Redis endpoints
    - CeleryExecutor
    - PVCs for DAGs/logs
    - RBAC enabled
    - Flower enabled (optional)
    - Resource requests/limits
    - SecurityContext (non-root)
    - Liveness/readiness probes
    - Ingress for webserver
    - Connections/variables via Secret or Helm values
- **Reason:** Simplifies deployment and maintenance.

### Step 8: Configure Ingress Controller
- **Why:** Securely expose Airflow UI/API.
- **What:**
  - Use NGINX, Traefik, or cloud-native Ingress.
  - Enable TLS/HTTPS.
- **Reason:** Protects UI and API endpoints.

### Step 9: Set Up Monitoring & Alerting
- **Why:** Detect issues, track performance.
- **What:**
  - Deploy Prometheus (metrics), Grafana (dashboards), Alertmanager (notifications).
  - Use Airflow metrics exporter.
- **Reason:** Enables proactive operations and troubleshooting.

### Step 10: Set Up Backups
- **Why:** Prevent data loss.
- **What:**
  - Automate Postgres backups (pgBackRest, cloud snapshots).
  - Backup DAGs/logs to S3/GCS.
- **Reason:** Ensures disaster recovery.

### Step 11: Apply Network Policies
- **Why:** Restrict traffic for security.
- **What:**
  - Use Kubernetes NetworkPolicy to allow only necessary connections (e.g., webserver ingress, DB/Redis internal).
- **Reason:** Reduces attack surface.

### Step 12: Test & Validate
- **Why:** Ensure everything works as expected.
- **What:**
  - Run test DAGs, simulate failover, check scaling, validate monitoring/alerts.
- **Reason:** Confirms production readiness.

---

## 3. Example Helm Values (Enterprise)

```yaml
# airflow/values.yaml (key sections)
postgresql:
  enabled: false
externalDatabase:
  type: postgresql
  host: <postgres-service>
  port: 5432
  database: airflow
  user: airflow
  passwordSecret: airflow-db-secret

redis:
  enabled: false
externalRedis:
  host: <redis-service>
  port: 6379
  passwordSecret: airflow-redis-secret

dags:
  persistence:
    enabled: true
    existingClaim: airflow-dags-pvc

logs:
  persistence:
    enabled: true
    existingClaim: airflow-logs-pvc

webserver:
  service:
    type: ClusterIP
  ingress:
    enabled: true
    hosts:
      - airflow.example.com
    tls:
      - secretName: airflow-tls

scheduler:
  resources:
    requests:
      cpu: 500m
      memory: 1Gi
    limits:
      cpu: 1
      memory: 2Gi

workers:
  replicas: 3
  resources:
    requests:
      cpu: 500m
      memory: 1Gi
    limits:
      cpu: 1
      memory: 2Gi

rbac:
  create: true

flower:
  enabled: true

airflowUser: 50000

# Monitoring
prometheus:
  enabled: true
grafana:
  enabled: true
```

### Helm Values Explanation

- **postgresql.enabled: false** — Disables the built-in Postgres; you use an external, HA Postgres deployment.
- **externalDatabase** — Connection details for your external Postgres DB. `passwordSecret` references a Kubernetes Secret for security.
- **redis.enabled: false** — Disables the built-in Redis; you use an external, HA Redis deployment.
- **externalRedis** — Connection details for your external Redis broker. `passwordSecret` references a Kubernetes Secret for security.
- **dags.persistence.enabled: true** — Enables persistent storage for DAGs (workflows). `existingClaim` points to a pre-created PVC or storage class.
- **logs.persistence.enabled: true** — Enables persistent storage for logs. `existingClaim` points to a pre-created PVC or storage class.
- **webserver.service.type: ClusterIP** — Internal service; exposed externally via Ingress.
- **webserver.ingress.enabled: true** — Enables Ingress for secure, external access to the Airflow UI/API. `hosts` and `tls` configure domain and HTTPS.
- **scheduler.resources / workers.resources** — Requests and limits for CPU/memory to ensure performance and prevent resource starvation.
- **workers.replicas: 3** — Number of Celery workers for parallel task execution; scale as needed.
- **rbac.create: true** — Enables Kubernetes RBAC for security and least privilege.
- **flower.enabled: true** — Deploys Flower dashboard for monitoring Celery workers.
- **airflowUser: 50000** — Runs Airflow containers as a non-root user for security.
- **prometheus.enabled / grafana.enabled: true** — Enables monitoring and dashboards for metrics and alerting.

---

## 4. Best Practices Checklist

- [x] Use external, HA Postgres and Redis
- [x] Store DAGs/logs on PVC or object storage
- [x] Secure all secrets (Vault/KMS/K8s Secrets)
- [x] Enable RBAC and NetworkPolicy
- [x] Use Ingress with TLS
- [x] Set resource requests/limits
- [x] Enable liveness/readiness probes
- [x] Monitor with Prometheus/Grafana
- [x] Automate backups
- [x] Test failover and scaling

---

## 5. References

- [Airflow Helm Chart Docs](https://airflow.apache.org/docs/helm-chart/stable/index.html)
- [Kubernetes Best Practices](https://kubernetes.io/docs/concepts/configuration/overview/)
- [Zalando Postgres Operator](https://github.com/zalando/postgres-operator)
- [Prometheus Operator](https://github.com/prometheus-operator/prometheus-operator)
- [Vault Helm Chart](https://github.com/hashicorp/vault-helm)

---

## 6. FAQ & Tips

**Q: How do I scale Airflow workers?**
A: Edit `workers.replicas` in Helm values and run `helm upgrade`.

**Q: How do I update secrets?**
A: Use your secrets manager (Vault/KMS) or update K8s Secret and redeploy.

**Q: How do I monitor Airflow?**
A: Enable Prometheus/Grafana in Helm values; use Airflow metrics exporter.

**Q: How do I back up DAGs/logs?**
A: Use PVC snapshots or sync to S3/GCS with a cron job.

**Q: How do I enable HTTPS for the UI?**
A: Configure Ingress with TLS and provide a certificate secret.

**Q: How do I test failover?**
A: Simulate pod/node failure; verify auto-recovery and DB/data integrity.

---

**For more details, see `docs/ARCHITECTURE.md`, `docs/HELM_MIGRATION.md`, and `kubernetes/README.md`.**
