# 🚀 Airflow on Azure Kubernetes Service - Getting Started

**Welcome to your Airflow POC!** This repository is configured to run Apache Airflow on Azure Kubernetes Service (AKS) with enterprise integrations.

---

## ⚡ Quick Start (5 Minutes)

If you're in a hurry:

1. **Deploy Airflow:**
```powershell
helm install airflow apache-airflow/airflow -n airflow --create-namespace -f kubernetes/values.yaml
```

2. **Access it:**
```powershell
$IP = kubectl get svc airflow-webserver -n airflow -o jsonpath='{.status.loadBalancer.ingress[0].ip}'
Write-Host "http://$IP:8080"
```

👉 **Full details:** See [`QUICKSTART.md`](./QUICKSTART.md)

---

## 📚 Documentation By Use Case

### 🎯 I want to deploy Airflow to AKS
- **Start here:** [`QUICKSTART.md`](./QUICKSTART.md) - 5-minute setup
- **Full guide:** [`AKS_DEPLOYMENT_GUIDE.md`](./AKS_DEPLOYMENT_GUIDE.md) - Complete instructions
- **Summary:** [`SETUP_CLEANUP_SUMMARY.md`](./SETUP_CLEANUP_SUMMARY.md) - What changed in cleanup

### 🔗 I want to connect to enterprise systems

Pick the integration you need:

- **Azure (Blob Storage, Data Lake, etc.):**  
  [`AZURE_CONNECTIONS_SETUP.md`](./AZURE_CONNECTIONS_SETUP.md)

- **Databricks (Jobs, Notebooks, SQL):**  
  [`DATABRICKS_CONNECTION_SETUP.md`](./DATABRICKS_CONNECTION_SETUP.md)

- **PowerBI (Dataset refresh, reports):**  
  [`POWERBI_CONNECTION_SETUP.md`](./POWERBI_CONNECTION_SETUP.md)

- **On-Premises SQL Server (ODBC, MSSQL):**  
  [`ONPREM_SQLSERVER_SETUP.md`](./ONPREM_SQLSERVER_SETUP.md)

### 📖 I want to learn Airflow basics
- **DAG basics:** See example DAGs in `dags/` folder
- **Architecture:** [`ARCHITECTURE.md`](./ARCHITECTURE.md)

### 🔍 I need to troubleshoot something
- Each connection guide has a **Troubleshooting** section
- Check Kubernetes logs: `kubectl logs -n airflow deployment/airflow-scheduler -f`
- Access pod: `kubectl exec -it -n airflow deployment/airflow-scheduler -- /bin/bash`

---

## 🗺️ Complete Documentation Map

```
docs/
├── 📄 QUICKSTART.md                    ← START HERE (5 min)
├── 📄 AKS_DEPLOYMENT_GUIDE.md          ← Full AKS setup
├── 📄 SETUP_CLEANUP_SUMMARY.md         ← What changed
│
├── 🔗 Connection Guides:
├── 📄 AZURE_CONNECTIONS_SETUP.md
├── 📄 DATABRICKS_CONNECTION_SETUP.md
├── 📄 POWERBI_CONNECTION_SETUP.md
├── 📄 ONPREM_SQLSERVER_SETUP.md
│
└── 📚 Reference:
    ├── 📄 ARCHITECTURE.md              ← System design
    └── 📄 00_START_HERE.md             ← This file
```

---

## 💡 What's Included

Your AKS Airflow setup has:

✅ **Pre-configured providers:**
- Apache Airflow Providers for Azure, Databricks, MSSQL, ODBC
- All database connectors and data processing libraries

✅ **Production-ready infrastructure:**
- CeleryExecutor (distributed task execution)
- PostgreSQL backend database
- Redis broker for task queuing
- Kubernetes deployment with auto-scaling

✅ **Comprehensive documentation:**
- Step-by-step setup guides
- Integration examples for each provider
- Troubleshooting help
- Performance optimization tips

✅ **Example DAGs:**
- Located in `dags/` folder
- Organized by integration type (azure/, databricks/, powerbi/, onprem/)

---

## 🚀 Common Workflows

### 1. Deploy and Access Airflow
See: [`QUICKSTART.md`](./QUICKSTART.md) - 5 minutes

### 2. Configure a Connection
Choose guide above based on what you're connecting to

### 3. Create a DAG
1. Create file in `dags/` folder
2. Airflow auto-detects it (usually within 1-2 minutes)
3. Enable in UI and run

### 4. Monitor Execution
- Airflow Web UI: `http://<IP>:8080`
- Kubernetes: `kubectl get pods -n airflow`
- Logs: `kubectl logs -n airflow deployment/airflow-scheduler -f`

---

## 🔑 Key Points

- **No Docker builds needed** - Use Helm chart
- **Automatic provider installation** - Configured in `kubernetes/values.yaml`
- **DAG hot-loading** - Changes auto-load, no redeploy needed
- **Scalable** - Adjust worker count for workload
- **Secure** - All credentials in Connections (encrypted)

---

## 📋 Checklist to Get Started

- [ ] AKS cluster ready and `kubectl` configured
- [ ] Helm installed (3+)
- [ ] Read [`QUICKSTART.md`](./QUICKSTART.md)
- [ ] Run `helm install` command
- [ ] Access Airflow UI
- [ ] Configure connections for your integrations
- [ ] Deploy your first DAG
- [ ] Monitor and iterate

---

## 💬 Common Questions

**Q: Do I need to build a Docker image?**  
A: No! Helm handles everything. All providers configured in `kubernetes/values.yaml`

**Q: How do I add a new provider?**  
A: Edit `kubernetes/values.yaml` → add to `extraPipPackages` → run `helm upgrade`

**Q: Where do I put my DAGs?**  
A: In the `dags/` folder. Airflow auto-detects them.

**Q: How do I connect to my on-premises SQL Server?**  
A: See [`ONPREM_SQLSERVER_SETUP.md`](./ONPREM_SQLSERVER_SETUP.md) for network setup and connection details

**Q: Can I scale the workers?**  
A: Yes! Edit `kubernetes/values.yaml` or use: `helm upgrade airflow ... --set workers.replicas=5`

---

## 🎯 Next Steps

1. **Choose your path above** based on what you need
2. **Read the relevant documentation**
3. **Follow the step-by-step instructions**
4. **Test your connections**
5. **Start building DAGs!**

---

## 📞 Support Resources

- [Apache Airflow Docs](https://airflow.apache.org/docs/)
- [AKS Documentation](https://docs.microsoft.com/en-us/azure/aks/)
- [Kubernetes Docs](https://kubernetes.io/docs/)
- [Airflow Helm Chart](https://airflow.apache.org/docs/helm-chart/stable/)

### Step 3️⃣: Learn the Fundamentals
📚 **Read:** [`AIRFLOW_BASICS.md`](./AIRFLOW_BASICS.md)
- What is a DAG, anyway?
- How do tasks work?
- Operators, schedules, and dependencies explained

**Time:** 1-2 hours | **Difficulty:** 🟡 Core concepts

---

## 📂 Navigation Hub

### 🎯 Quick Access

| Document | Purpose | When to Use |
|----------|---------|-------------|
| [`INDEX.md`](./INDEX.md) | 🗂️ Complete documentation map | Need to find something specific |
| [`FOLDER_STRUCTURE.md`](./FOLDER_STRUCTURE.md) | 📁 Where everything lives | Adding new files or organizing code |
| [`LEARNING_CHECKLIST.md`](./LEARNING_CHECKLIST.md) | ✅ Track your progress | Stay motivated and on track |
| [`SETUP_SUMMARY.md`](./SETUP_SUMMARY.md) | ⚙️ Configuration details | Troubleshooting or customizing |
| [`HELM_MIGRATION.md`](./HELM_MIGRATION.md) | 🎡 Moving to production | Ready to use Helm charts |

---

## 🎓 Recommended Learning Order

```
Week 1: Getting Started
├─ 📖 ARCHITECTURE.md (understand the big picture)
├─ ⚡ QUICKSTART.md (get it running)
└─ 📚 AIRFLOW_BASICS.md (learn core concepts)

Week 2: Building Pipelines
├─ 🔧 Run the example DAGs
├─ 🛠️ Modify them
└─ 🏗️ Create your first custom DAG

Week 3: Going Deeper
├─ 📁 FOLDER_STRUCTURE.md (organize properly)
├─ 🔒 SECRETS_MANAGEMENT.md (handle credentials)
└─ 🧪 Write tests for your DAGs

Week 4+: Production Ready
├─ 🎡 HELM_MIGRATION.md (deploy with Helm)
├─ 🔧 SETUP_SUMMARY.md (fine-tune configuration)
└─ 📊 Monitor and optimize
```

---

## 💡 Pro Tips

> **First time with Airflow?** Start with `ARCHITECTURE.md` to see the whole picture, then jump into `QUICKSTART.md` to get hands-on immediately. Reading without doing gets boring fast!

> **Stuck on something?** Check the troubleshooting sections in each guide. If that doesn't help, the logs are your best friend: `kubectl logs -n airflow <pod-name>`

> **Want to dive deep?** The `LEARNING_CHECKLIST.md` has a structured path from beginner to advanced with checkboxes to track your progress.

---

## 🆘 Need Help?

**Common Starting Points:**
- 🚫 **Can't access the UI?** → See [QUICKSTART.md - Troubleshooting](./QUICKSTART.md#troubleshooting)
- 🔍 **DAGs not showing up?** → See [SETUP_SUMMARY.md - Verify DAG Discovery](./SETUP_SUMMARY.md#verify-dag-discovery)
- 🔐 **Credentials not working?** → See [SECRETS_MANAGEMENT.md](./SECRETS_MANAGEMENT.md)
- 📂 **Where do I put my code?** → See [FOLDER_STRUCTURE.md](./FOLDER_STRUCTURE.md)

---

## 🎯 What's Next?

1. **If you haven't deployed yet:** Go to → [`QUICKSTART.md`](./QUICKSTART.md)
2. **If Airflow is running:** Go to → [`AIRFLOW_BASICS.md`](./AIRFLOW_BASICS.md)
3. **If you want to understand the architecture:** Go to → [`ARCHITECTURE.md`](./ARCHITECTURE.md)
4. **If you're ready to build:** Go to → [`LEARNING_CHECKLIST.md`](./LEARNING_CHECKLIST.md)

---

## 📚 More Resources

The root [`README.md`](../README.md) in the repository provides a high-level overview of the entire project.

---

**Ready to become an Airflow pro?** Let's go! 🚀

*Remember: Learning is a journey, not a race. Take your time, experiment, and don't be afraid to break things (that's what POCs are for!)*
