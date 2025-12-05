# ⚡ Enterprise Data Orchestration Improvements

Optimize your data workflows! This guide identifies current pain points and recommends improvements for enterprise orchestration. 🎯

> **💡 Focus:** Moving from time-based to event-driven workflows, reducing latency, improving reliability

## 1️⃣ Current Flow & Pain Points

Flow: On-Prem Sources → ADF ingestion → ADLS (Raw/Landing) → Databricks Workflows (Bronze/Silver/Gold) → Time-based refresh → Power BI semantic models.

Key Challenges:
- Integration Handshake: Manual / brittle triggering between ADF → Databricks → Power BI; limited event propagation.
- Control & Dependency Management: Cross-tool dependencies handled by ad-hoc schedules (time-based), causing race conditions when upstream delays occur.
- Monitoring & Observability: Fragmented logs (ADF vs Databricks vs Power BI) with no unified run ID or lineage path; difficult root cause analysis.
- Retry / Idempotency: Partial failures create orphaned intermediate data; lack consistent idempotent write patterns (merge-overwrite or ACID tables) across layers.
- Governance: Data quality checks often embedded inside notebooks rather than centrally enforced; limited metadata-driven configuration.
- SLA Management: No unified SLA registry; escalation and alerting inconsistent.

## 2. Design Principles

1. Event-Driven First: Prefer events over timers for inter-stage transitions (e.g., ingestion completion triggers transform start).
2. Asset-Centric View: Treat data sets (tables/files/models) as assets with declared upstream dependencies.
3. Unified Orchestration Abstraction: One control-plane defines DAG/graph, even if execution spans multiple platforms.
4. Idempotent, Declarative Jobs: Each stage safe to re-run; writes use MERGE, COPY INTO with checkpointing or Delta ACID transactions.
5. Observability & Lineage as a First-Class Feature: Every run emits standardized structured events (start, success, fail) with correlation IDs.
6. Shift from Time-Based Power BI Refresh to Data-Ready Triggers: Refresh only when Gold-layer (or semantic model input) assets updated and validated.

## 3. Orchestration Option Matrix

| Option | Strengths | Gaps / Risks | Best Fit Scenario |
|--------|-----------|--------------|-------------------|
| Airflow (K8s) | Mature DAG, plugins, cross-system orchestration, Python extensibility | Requires infra ops; native Azure integration via hooks not as seamless as ADF | Multi-source, poly-cloud, complex dependencies |
| Azure Data Factory-only | Native ingestion / scheduling, managed service | Weaker for downstream asset-based transformation & complex branching; limited lineage | Primarily ingestion orchestration with simple transform triggers |
| Databricks Workflows centralization | Tight integration with Delta & ML; simple job dependencies | External system triggers (ADF / Power BI) need API bridging; limited global lineage | Heavy Databricks investment; majority of logic inside lakehouse |
| Synapse Pipelines | Unified SQL + Spark + ingestion; Azure native | Less mature vs dedicated tools; migration overhead | Desire a single Azure-native workspace |
| Prefect 2.0 | Cloud/Rich orchestration, dynamic work, easy Python APIs | Requires connectors for Azure services; custom lineage | Need lightweight orchestration with modern workflow semantics |
| Dagster | Asset-based, declarative dependencies & lineage; powerful for data mesh | Operational learning curve; hosting required (unless Dagster Cloud) | Strong need for asset-level lineage & data contracts |
| Temporal | Durable, long-lived workflows, retries, state recovery | Requires significant engineering; not data-specific; no native lineage | Complex, mission-critical workflows that must survive infra failures |
| Microsoft Fabric | Unified lakehouse + Power BI + Data Activator | Emerging platform; migration complexity; licensing | Strategic alignment with Fabric vision |

## 4. Recommended Hybrid Architecture

Short Term (Incremental): Introduce central orchestration layer while retaining native services for execution.
- ADF remains ingestion engine (copy/on-prem integration) but publishes completion events to Azure Event Grid.
- Databricks Jobs/Workflows subscribe via an event-driven trigger (Azure Function or Logic App mediator) instead of cron.
- Gold-layer completion emits event including asset metadata (table name, version, quality status) to Event Grid.
- Orchestrator (Airflow or Dagster or Prefect) listens to events and governs Power BI dataset refresh via REST / XMLA only if quality gates passed.

Medium Term:
- Move transformation dependencies into asset graph (Dagster assets or Airflow DAG with task mapping) enabling conditional, parallel runs.
- Implement metadata-driven config (YAML/JSON in Git) for source → target mapping, SLAs, quality rules.

Long Term:
- Consolidate to either Dagster (asset-first) or Airflow (broad ecosystem) depending on organizational skills; adopt OpenLineage or DataHub for lineage, and Purview for catalog integration.
- Integrate data contracts (schema + expectations) validated automatically at each stage.

## 5. Handshake / Trigger Patterns

Pattern A: Event-Grid Mediated
1. ADF pipeline success -> Custom event to Event Grid (contains `runId`, `sourceSystem`, `landingPath`).
2. Azure Function receives event -> Calls orchestrator API (Airflow REST or Prefect) to start transformation flow with payload.
3. Databricks job tasks emit structured completion events (including Delta table version and expectation results).
4. Orchestrator evaluates quality gates; on pass triggers Power BI refresh (`POST https://api.powerbi.com/v1.0/myorg/groups/{groupId}/datasets/{datasetId}/refreshes`).

Pattern B: Asset Pull (Dagster)
- Sensor polls for new ingestion asset (raw partition) registered via ADF output manifest.
- Materialization triggers downstream asset builds automatically; lineage recorded.

Pattern C: Unified Job API (Databricks-centered)
- ADF completion triggers Databricks multi-task job via Jobs API.
- Terminal task invokes webhook to orchestrator for Power BI conditional refresh.

Reliability Enhancements:
- Use correlation ID propagated: ADF runId → Orchestrator task instance → Databricks job run → Power BI refresh request.
- Idempotency: Each stage writes to Delta tables using partition overwrite + commit, or MERGE keyed on natural/business keys to allow safe reruns.
- Retry Policies: Exponential backoff for transient API failures, circuit-breaker for repeated data quality failures.

## 6. Observability & Lineage

Components:
- Structured Event Envelope: `{timestamp, correlationId, stage, status, durationMs, dataAssets:[...], quality:{passed, failedTests}}` to Event Hub / Log Analytics.
- Metrics: Latency per stage, success rate, data freshness (current_time - last_success_timestamp), SLA breach counter.
- Dashboards: Azure Monitor Workbook or Grafana (if Airflow metrics exporter) combining ingestion, transform, BI refresh.
- Lineage: OpenLineage emitters in Airflow/Dagster + Databricks; ingest into DataHub or Purview for searchable lineage; link Power BI dataset to upstream Delta tables via Purview scanning.
- Alerting: Define SLA object storage (e.g., `slo.yaml`) driving alert generation (Azure Monitor metrics alert or PagerDuty).

## 7. Governance & Data Quality

- Data Contracts: JSON schema + expectation definitions (Great Expectations or Pandera) version-controlled.
- Quality Enforcement: Transform task executes expectations; fails early and emits failure event; orchestrator halts downstream refresh.
- Access Controls: Use ABAC/RBAC through ADLS ACLs, Unity Catalog (Databricks), Purview classification.
- Versioning: Tag Delta tables with semantic versions (table property `asset_version`), propagate to Power BI semantic model description.
- Change Management: Pull request validation pipeline runs contract diff + test data sample.

## 8. Migration Roadmap

Phase 0: Instrument current pipelines with correlation IDs & structured logs (low risk).
Phase 1: Add Event Grid events on ADF success; build small orchestrator function triggering Databricks.
Phase 2: Introduce orchestrator (Airflow/Dagster/Prefect) for cross-system dependencies; migrate Power BI refresh logic.
Phase 3: Implement asset graph & metadata-driven configs; adopt quality contracts.
Phase 4: Deploy lineage stack (OpenLineage emitters + DataHub/Purview integration).
Phase 5: Optimize & decommission redundant cron schedules; fully event-driven.

## 9. Tool Selection Guidance

Choose Airflow if:
- Need broad ecosystem (SFTP, legacy APIs, mixed clouds).
- Team already deploying Airflow (as evidenced by current POC).

Choose Dagster if:
- Asset-level lineage & declarative dependencies are priority.
- Engineering capacity for adopting new paradigm.

Choose Prefect if:
- Desire managed orchestration with quick onboarding.
- Need dynamic, parameterized flows with minimal infra.

Choose Databricks Workflows centric if:
- Majority of transformation/ML inside Databricks and ingestion minimal.

Choose Fabric (strategic future) if:
- Organizational initiative to unify analytics platform.

## 10. Power BI Refresh Modernization

Replace time-based refresh with conditional triggers:
1. Gold asset event includes `quality.passed=true`, `asset_version`, `dataset_mapping`.
2. Orchestrator checks dataset staleness (compare last model refresh vs asset_version).
3. If stale & within refresh policy window, call Power BI REST; poll status; emit completion/latency metric.
4. Failure -> automatic retry window + notification.

## 11. Reference Implementation Sketch (Airflow)

- Ingestion Sensor DAG: ExternalTaskSensor or custom Event Grid sensor waiting on ADF completion event.
- Transformation DAG: Dynamic task mapping over changed partitions; tasks wrap Databricks Jobs API call.
- Quality Task: PythonOperator invoking expectations stored in `/expectations/<asset>.json`.
- Conditional BI Refresh Task: BranchPythonOperator deciding refresh; HttpOperator performs REST call.
- Lineage: OpenLineage backend configured via `airflow.cfg` or environment variables.

## 12. KPIs After Implementation

- End-to-End Freshness < Target SLA (e.g., 45 min) 95% of days.
- Mean Time to Detect (MTTD) pipeline failure reduced by >50%.
- Manual restarts decreased by >70% via idempotency.
- Traceability: >90% of assets with upstream lineage path resolvable in catalog.

## 13. Next Actions

1. Decide orchestrator (pilot Airflow vs Dagster comparison within 2 weeks).
2. Implement Event Grid emission on ADF success (POC in dev subscription).
3. Add correlation ID spec & logging library wrapper.
4. Build minimal lineage pipeline (OpenLineage + DataHub docker compose) for dev.
5. Draft data contract template and apply to two critical gold tables.
6. Replace one Power BI dataset's scheduled refresh with event-driven.

---

This document provides a strategic and tactical path to move from time-based, fragmented orchestration toward an event-driven, observable, governed data platform.
