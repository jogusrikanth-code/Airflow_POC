# Airflow POC

Welcome to the Airflow Proof of Concept repository! This project demonstrates running Apache Airflow on Kubernetes with enterprise integration patterns. 🚀

## 🚀 Quick Start

Deploy Airflow to Kubernetes (Docker Desktop):

```powershell
# Deploy all Airflow components
kubectl apply -f kubernetes/airflow.yaml

# Check deployment status
kubectl get pods -n airflow

# Access the Airflow UI at http://localhost:8080
kubectl port-forward svc/airflow-webserver 8080:8080 -n airflow
```

Create admin credentials and start building workflows! See [QUICKSTART.md](docs/QUICKSTART.md) for detailed setup.

## 📚 Documentation

All comprehensive guides are in the `docs/` folder. **Start here:** [docs/README.md](docs/README.md)

**Quick Navigation:**
- 🎓 **New to Airflow?** → [AIRFLOW_BASICS.md](docs/AIRFLOW_BASICS.md)
- ⚡ **Deploy Now** → [QUICKSTART.md](docs/QUICKSTART.md)
- 🔧 **Setup Reference** → [SETUP_SUMMARY.md](docs/SETUP_SUMMARY.md)
- 🏗️ **Architecture** → [ARCHITECTURE.md](docs/ARCHITECTURE.md)
- 🏢 **Enterprise Deployment** → [ENTERPRISE_ARCHITECTURE.md](docs/ENTERPRISE_ARCHITECTURE.md)
- 🔗 **Integrations (Databricks, Power BI)** → [ENTERPRISE_INTEGRATION.md](docs/ENTERPRISE_INTEGRATION.md)

## 💡 What's Included

This POC demonstrates:
- ✅ Kubernetes deployment with PostgreSQL + Redis
- ✅ Multiple deployment options (Helm + git-sync or hostPath)
- ✅ Enterprise connectors (Databricks, Power BI, Azure, On-Premises)
- ✅ ETL pipeline examples with real data processing
- ✅ Comprehensive documentation for learning and production deployment

## 📊 Example DAGs

- **`demo_dag.py`** - Simple 2-task workflow for learning DAG basics
- **`etl_example_dag.py`** - Full ETL pipeline (extract, transform, load) with sample CSV data
- **`enterprise_integration_dag.py`** - Production-style integration: On-Premises → Azure → Databricks → Power BI

## 🗂️ Database Queries

Use **`airflow_queries.sql`** for debugging Airflow's PostgreSQL database:
- DAG status and run history
- Failed task analysis
- Performance metrics
- XCom data inspection

See [POSTGRES_VSCODE_CONNECTION.md](docs/POSTGRES_VSCODE_CONNECTION.md) for connection setup.

## 📁 Folder Structure

```
Airflow_POC/
├── README.md                     # Project overview (this file)
├── airflow_queries.sql           # SQL queries for debugging
├── docs/                         # 📚 Complete documentation (19 guides)
├── dags/                         # Airflow DAG definitions
├── src/                          # Python source code
│   ├── connectors/               # Enterprise connectors (Azure, Databricks, Power BI)
│   ├── extract/                  # Data extraction modules
│   ├── transform/                # Data transformation logic
│   └── load/                     # Data loading utilities
├── plugins/                      # Custom Airflow plugins
├── kubernetes/                   # K8s deployment manifests
├── data/                         # Sample data files
│   ├── raw/                      # Source data
│   └── processed/                # Transformed data
├── scripts/                      # Setup and utility scripts
└── archive/                      # Historical files for reference
```

## ⚙️ Common Commands

```powershell
# View all pods
kubectl get pods -n airflow

# Check logs
kubectl logs -n airflow deploy/airflow-scheduler -f
kubectl logs -n airflow deploy/airflow-webserver -f

# Port-forward to database (for querying)
kubectl port-forward -n airflow pod/postgres-0 5432:5432
```

**Troubleshooting?** Check [QUICKSTART.md](docs/QUICKSTART.md) for detailed debugging steps.

---

**Ready to get started?** Head to [docs/README.md](docs/README.md) for your personalized learning path! 🎓
