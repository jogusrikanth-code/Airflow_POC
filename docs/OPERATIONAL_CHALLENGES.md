# 🐛 Operational Challenges & Real-World Solutions

Running Airflow in production? Here are the challenges you'll face and practical ways to handle them. Learn from real-world experience! 🎯

> **💡 Pro Tip:** Read this BEFORE going to production. An ounce of prevention is worth a pound of cure!

## 🎯 Scope
- Compute: On‑prem Kubernetes (scheduler, webserver, workers, triggerer, Redis, Postgres)
- Storage: Azure Blob Storage for task/webserver logs (remote logging)
- Networking: On‑prem → Azure over VPN/ExpressRoute

## Infrastructure (On‑Prem)
- Hardware failures: Nodes can crash; no cloud auto‑healing. Keep spares and run HA scheduler.
- Capacity planning: Size for peak; frequent idle waste. Consider autoscaling add‑ons.
- Maintenance windows: OS/K8s patching interrupts DAGs; schedule and communicate downtime.
- Storage bottlenecks: Local SAN/NAS performance can degrade DB/log writes; monitor IOPS/latency.
- Resource contention: Shared clusters cause noisy neighbors; isolate with taints/quotas.

## Scaling & Reliability
- Fixed capacity: No burst to cloud; provision for worst‑case.
- Slow node add: Physical procurement → racking → config takes time.
- Autoscaling gaps: HPA/KEDA need careful metrics; avoid thrashing.
- Single points: Scheduler/DB are critical; deploy at least 2 schedulers and HA Postgres.
- Zombie tasks: Worker crashes mid‑task; enforce idempotency and retries.

## Hybrid Networking (On‑Prem ↔ Azure)
- Latency: 20–100 ms typical; every log write adds WAN round‑trip.
- Bandwidth saturation: Large concurrent runs can saturate circuits; throttle/ batch log writes.
- VPN/ExpressRoute stability: Disconnects drop log uploads; implement retry and local buffering.
- DNS/private endpoints: Ensure proper resolution for `*.blob.core.windows.net` and Private DNS if used.
- Firewall rules: Allow outbound HTTPS to Azure Storage; review service tags and proxies.

## Azure Blob Logs (Remote Logging)
- Write performance: High log frequency + WAN latency → slow tasks; prefer buffered, batched writes.
- Read performance: UI log fetches over WAN feel sluggish; avoid excessive UI tailing.
- Throttling: Storage account request limits can be hit at peak; shard per environment.
- Lifecycle & retention: Rules apply daily; not instant. Plan cool/archive tiers and rehydration time.
- Egress costs: Reading many logs for debugging incurs per‑GB charges.

## Security & Identity
- No managed identity: On‑prem pods can’t use Azure Workload Identity. Use SAS tokens or account keys.
- Key rotation: Rotate SAS/account keys regularly; restart workers to pick up new creds.
- Secrets handling: Store tokens in Kubernetes Secrets; avoid plaintext in ConfigMaps or images.
- Data sensitivity: Logs may contain PII/PHI; sanitize task logging and enforce retention.

## Database (Postgres)
- Growth: `task_instance`, logs, XComs grow fast. Schedule cleanup and archiving.
- Performance: Tune connections, indexes, autovacuum; consider PgBouncer.
- Backups/DR: Test PITR restore; define RPO/RTO; store backups off‑cluster.

## Observability
- Split monitoring: On‑prem (nodes/pods/DB) + Azure Storage (requests/latency/errors).
- Alerts: Create alerts for Azure upload failures, high write latency, DB pressure, scheduler health.
- Log aggregation: Consider local PV + sidecar uploader for resilient logging and local grep.

## Cost Considerations (Azure Logs)
- Operations cost: Writes/listings/deletes billed; estimate per task run volume.
- Egress: Debug downloads add up; minimize large log reads.
- Storage tiering: Use lifecycle to move to Cool after 30 days; delete after 90.

## Practical Mitigations
- Local buffering: Write logs to local PV first; sidecar syncs to Azure asynchronously with retries.
- Circuit breaker: If Azure unavailable, continue with local logs and flag uploads for retry.
- Secrets: Use Kubernetes Secrets; rotate SAS tokens; scope permissions minimally (write‑only).
- Scheduler/DB HA: 2+ schedulers, HA Postgres, Redis durability; periodic health checks.
- Resource isolation: Dedicated worker node pool with taints; quotas/limits per namespace/team.
- Cleanup jobs: Regularly purge old task instances, logs, and XComs; enforce DAG log retention.
- Monitoring stack: Prometheus/Grafana for Airflow metrics; Azure Monitor for Storage; alert rules.

## Example Config Snippets

Remote logging (Helm values):

```
config:
  logging:
    remote_logging: 'True'
  core:
    remote_base_log_folder: "wasb://logs@<storage-account>.blob.core.windows.net/airflow"
    remote_log_conn_id: "azure_blob_logs"
```

Lifecycle policy (PowerShell):

```
az storage account management-policy create `
  --account-name <account> `
  --policy '{
    "rules": [{
      "name":"logs-tiering",
      "type":"Lifecycle",
      "definition":{
        "filters": {"blobTypes":["blockBlob"], "prefixMatch":["airflow/"]},
        "actions": {"baseBlob": {"tierToCool": {"daysAfterModificationGreaterThan": 30},
                                    "delete": {"daysAfterModificationGreaterThan": 90}}}
      }
    }]}'
```

Worker node isolation (AKS example concept, similar for on‑prem schedulers):

```
nodeSelector:
  role: airflow-worker
tolerations:
  - key: "airflow-worker"
    operator: "Equal"
    value: "true"
    effect: "NoSchedule"
```

## Runbook Highlights
- Azure outage: Switch to local logs; queue uploads; notify stakeholders.
- SAS/key rotation: Update Secret → rollout restart workers; verify uploads.
- DB hotspot: Scale Postgres vertically; enable PgBouncer; add indexes; cleanup.
- Scheduler stall: Restart scheduler pods; check DAG parsing/import errors.

## Summary
On‑prem Kubernetes offers control and compliance, while Azure Blob provides scalable log storage. The trade‑offs are hybrid networking complexity, log latency, and dual monitoring. With local buffering, robust secrets handling, HA components, and clear lifecycle/cost controls, the setup can be reliable and cost‑effective for enterprise POCs and steady‑state workloads.
