# Airflow on Kubernetes — Architecture & Beginner Guide

This guide explains, in plain English, how Airflow runs on Kubernetes, what each component does, and gives you a simple, step-by-step procedure with the why, what, and reasoning behind each step.

## High-Level Idea
- Airflow schedules and runs your workflows (DAGs).
- Kubernetes is the platform that hosts Airflow’s components as containers, keeps them healthy, and lets you scale.

## Components & Roles
- **Webserver**: The UI and control panel. You enable/trigger DAGs, view runs, and read logs.
- **Scheduler**: Reads DAG files and decides which tasks should run now; puts tasks onto a queue.
- **Worker(s)**: Pick tasks from the queue and execute your code (Python operators, etc.).
- **Redis**: The queue (Celery broker) that connects scheduler and workers.
- **PostgreSQL**: The metadata database; remembers DAG runs, task states, connections, variables.
- **DAGs/Plugins/Logs (Volumes)**: Your code and outputs shared so all components can read/write consistently.

## Visual Flow Diagram

```
           ┌────────────────────────────────────────────┐
           │            Kubernetes Cluster              │
           │             (Namespace: airflow)           │
           ├────────────────────────────────────────────┤
           │                                            │
           │  ┌───────────────┐        ┌────────────┐  │
UI → HTTP  │  │ Airflow        │        │ Scheduler  │  │
(you)      │  │ Webserver      │◄──────►│ (decides   │  │
           │  │ (Deployment)   │        │ what runs) │  │
           │  └──────▲─────────┘        └────▲───────┘  │
           │         │                        │          │
           │         │ reads DAGs             │ enqueues │
           │         │ & shows status         │ tasks    │
           │         │                        │          │
           │  ┌──────┴─────────┐     ┌────────┴──────┐  │
           │  │ DAGs/Plugins/  │     │ Redis (broker)│  │
           │  │ Logs (Volumes) │◄────┤ Queue         │  │
           │  └────────────────┘     └───────────────┘  │
           │                                            │
           │                  ┌────────────┐            │
           │                  │ Worker(s)  │◄───────────┘
           │                  │ Execute tasks from queue |
           │                  └────────────┘            │
           │                                            │
           │  ┌──────────────────────────────────────┐  │
           │  │ PostgreSQL (Metadata DB)             │  │
           │  │ DAG runs, task states, connections   │  │
           │  └──────────────────────────────────────┘  │
           │                                            │
           └────────────────────────────────────────────┘
```

## Kubernetes Building Blocks
- **Pods/Deployments/StatefulSets**: How components run (webserver, scheduler, worker, redis, postgres).
- **Services**: Stable addresses so components can talk (`postgres`, `redis`, `airflow-webserver`).
- **ConfigMaps**: Non-secret Airflow settings (e.g., executor type).
- **Secrets**: Sensitive values (database URL, celery broker URL).
- **Volumes**: Storage for DAGs and logs.
- **RBAC/ServiceAccount**: Permissions to run in the cluster.
- **Probes**: Health checks; Kubernetes restarts unhealthy pods automatically.

## Beginner Procedure (Why, What, Reasoning)

1) Prepare Kubernetes
- **Why**: Airflow needs a platform to run containers reliably.
- **What**: Enable Kubernetes in Docker Desktop; make sure `kubectl` works.
- **Reason**: K8s handles restarts, networking, and scaling for you.

2) Create Namespace & Secrets
- **Why**: Isolate resources; protect credentials.
- **What**: Use the `airflow` namespace; create the Secret with DB and broker URLs.
- **Reason**: Namespaces organize; Secrets keep passwords out of plain text configs.

3) Deploy PostgreSQL (Metadata DB)
- **Why**: Airflow tracks runs, task states, and settings in a database.
- **What**: Apply `kubernetes/postgres.yaml`; wait until ready.
- **Reason**: Without the DB, Airflow can’t remember anything long-term.

4) Deploy Redis (Celery Broker)
- **Why**: Connects scheduler and workers via a fast task queue.
- **What**: Included in `kubernetes/airflow.yaml`.
- **Reason**: Celery uses Redis; workers pull tasks from it.

5) Configure Airflow (ConfigMap + Secret)
- **Why**: Keep Airflow settings declarative and portable.
- **What**: Set executor (Celery), DAGs folder, broker/database URLs.
- **Reason**: Clean separation between images and environment-specific settings.

6) Deploy Airflow Components
- **Why**: Bring Webserver (UI), Scheduler (orchestration), Workers (execution) online.
- **What**: Apply `kubernetes/airflow.yaml`.
- **Reason**: You need all three to see UI, schedule, and execute tasks.

7) Validate Health
- **Why**: Catch issues early.
- **What**: `kubectl get pods`, `kubectl logs` (webserver/scheduler/worker).
- **Reason**: Ensures the stack is truly ready before using the UI.

8) Access Web UI
- **Why**: Operate Airflow (enable DAGs, trigger runs, inspect logs).
- **What**: Port-forward the webserver service.
  ```powershell
  kubectl port-forward svc/airflow-webserver 8080:8080 -n airflow
  # If 8080 is busy:
  kubectl port-forward svc/airflow-webserver 9090:8080 -n airflow
  ```
- **Reason**: Exposes the in-cluster service to your browser locally.

9) Run a DAG
- **Why**: Validate the full pipeline.
- **What**: Enable `demo_dag` or `etl_example_dag` in the UI; trigger; read logs.
- **Reason**: Confirms end-to-end: scheduler → redis → worker → DB state.

10) Scale or Troubleshoot
- **Why**: Adapt capacity; fix problems.
- **What**: Scale workers; check probes; view logs; describe pods.
  ```powershell
  kubectl scale statefulset/airflow-worker -n airflow --replicas=3
  ```
- **Reason**: Workloads vary; Kubernetes lets you grow or self-heal.

## Quick Reference (PowerShell)
```powershell
kubectl apply -f "kubernetes/postgres.yaml"
kubectl wait --for=condition=ready pod -l app=postgres -n airflow --timeout=300s
kubectl apply -f "kubernetes/airflow.yaml"
kubectl get pods -n airflow

kubectl port-forward svc/airflow-webserver 8080:8080 -n airflow
kubectl port-forward svc/airflow-webserver 9090:8080 -n airflow

kubectl logs -f deployment/airflow-webserver -n airflow
kubectl logs -f statefulset/airflow-scheduler -n airflow
kubectl logs -f statefulset/airflow-worker -n airflow
kubectl describe pod <pod-name> -n airflow
```

## Why Kubernetes Helps
- Resilience: Probes restart unhealthy pods.
- Scaling: Add workers easily when jobs increase.
- Separation: Independent components; safer upgrades.
- Observability: One place (`kubectl`) to check status and logs.

## See Also
- `docs/QUICKSTART.md` — Get running fast
- `kubernetes/README.md` — Deployment guide
- `docs/HELM_MIGRATION.md` — Switch to Helm
- `kubernetes/helm-values.yaml` — Helm values aligned to manifests
