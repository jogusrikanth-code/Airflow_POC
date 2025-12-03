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

All guides are in the `docs/` folder, now organized by deployment type and topic. **Start here:** [docs/README.md](docs/README.md)

**Quick Navigation:**
- 🎓 **New to Airflow?** → [docs/learning/AIRFLOW_BASICS.md](docs/learning/AIRFLOW_BASICS.md)
- ⚡ **Deploy on K8s** → [docs/deployment-guides/self-managed/QUICKSTART.md](docs/deployment-guides/self-managed/QUICKSTART.md)
- ☁️ **Deploy on AKS** → [docs/deployment-guides/aks/AKS_AIRFLOW_DEPLOYMENT_GUIDE.md](docs/deployment-guides/aks/AKS_AIRFLOW_DEPLOYMENT_GUIDE.md)
- 🌟 **Use Astronomer** → [docs/deployment-guides/astronomer/astronomer.md](docs/deployment-guides/astronomer/astronomer.md)
- 🔧 **Setup Reference** → [docs/deployment-guides/self-managed/SETUP_SUMMARY.md](docs/deployment-guides/self-managed/SETUP_SUMMARY.md)
- 🏗️ **Architecture** → [docs/learning/ARCHITECTURE.md](docs/learning/ARCHITECTURE.md)
- 🏢 **Enterprise Deployment** → [docs/enterprise/ENTERPRISE_ARCHITECTURE.md](docs/enterprise/ENTERPRISE_ARCHITECTURE.md)
- 🔗 **Integrations** → [docs/enterprise/ENTERPRISE_INTEGRATION.md](docs/enterprise/ENTERPRISE_INTEGRATION.md)

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

See [docs/deployment-guides/self-managed/POSTGRES_VSCODE_CONNECTION.md](docs/deployment-guides/self-managed/POSTGRES_VSCODE_CONNECTION.md) for connection setup.

## 📁 Folder Structure

```
Airflow_POC/
├── README.md                     # Project overview (this file)
├── airflow_queries.sql           # SQL queries for debugging
├── docs/                         # 📚 Organized documentation
│   ├── README.md                 # Documentation hub
│   ├── 00_START_HERE.md          # Personalized learning path
│   ├── learning/                 # Core concepts & tutorials
│   ├── deployment-guides/        # Deployment options
│   │   ├── self-managed/         # Self-managed K8s deployment
│   │   ├── aks/                  # Azure Kubernetes Service
│   │   └── astronomer/           # Managed Airflow platform
│   ├── enterprise/               # Production patterns & integrations
│   └── reference/                # Quick reference materials
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

**Troubleshooting?** Check [docs/deployment-guides/self-managed/QUICKSTART.md](docs/deployment-guides/self-managed/QUICKSTART.md) for detailed debugging steps.

---

**Ready to get started?** Head to [docs/README.md](docs/README.md) for your personalized learning path! 🎓
