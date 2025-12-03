# 🚀 Airflow POC — Documentation Hub

Hey there! Welcome to your comprehensive guide for deploying and mastering Apache Airflow. This folder has everything organized by deployment type and learning path! 🎯

## ⚡ Start Here (New to the Project?)

Perfect! Here's your fast track:

1️⃣ **[00_START_HERE.md](00_START_HERE.md)** → Your personalized learning path (15 min) 🗺️  
2️⃣ **[learning/ARCHITECTURE.md](learning/ARCHITECTURE.md)** → Understand how it all works (20 min) 🏗️  
3️⃣ **[deployment-guides/self-managed/QUICKSTART.md](deployment-guides/self-managed/QUICKSTART.md)** → Deploy Airflow on Kubernetes (30 min) 🚀  
4️⃣ **[learning/AIRFLOW_BASICS.md](learning/AIRFLOW_BASICS.md)** → Learn core concepts & build your first DAG (1-2 hrs) 📚

> **Pro Tip:** Don't skip 00_START_HERE! It'll save you hours by showing you exactly what to read based on your role and goals.

## 📂 Organized Documentation Structure

### 🎓 [learning/](learning/) - Learning & Getting Started
Perfect for newcomers and understanding core concepts:

- **`AIRFLOW_BASICS.md`** — Core concepts, tutorials, and hands-on examples 📖
- **`LEARNING_CHECKLIST.md`** — Track your progress from beginner to expert ✅
- **`ARCHITECTURE.md`** — System architecture and components explained 🏗️

### 🚀 [deployment-guides/](deployment-guides/) - Deployment Options
Choose your deployment path:

#### 📦 [self-managed/](deployment-guides/self-managed/) - Self-Managed Kubernetes
- **`QUICKSTART.md`** — Deploy to Kubernetes in 30 minutes ⚡
- **`HELM_MIGRATION.md`** — Migrate to official Helm charts 📦
- **`SETUP_SUMMARY.md`** — Configuration quick reference & access details 📋
- **`SECRETS_MANAGEMENT.md`** — Secure your credentials & sensitive data 🔐
- **`POSTGRES_VSCODE_CONNECTION.md`** — Connect to the Airflow database for debugging 💾

#### ☁️ [aks/](deployment-guides/aks/) - Azure Kubernetes Service
- **`AKS_AIRFLOW_DEPLOYMENT_GUIDE.md`** — Complete AKS production deployment guide 🏢

#### 🌟 [astronomer/](deployment-guides/astronomer/) - Managed Airflow
- **`astronomer.md`** — Astronomer managed platform option ☁️

### 🏢 [enterprise/](enterprise/) - Enterprise & Production
Production-ready patterns and optimization:

- **`ENTERPRISE_ARCHITECTURE.md`** — Production design with HA & DR 🏢
- **`ENTERPRISE_INTEGRATION.md`** — Connect to Databricks, Power BI, Azure services 🔗
- **`ENTERPRISE_POC_SUMMARY.md`** — Enterprise POC lessons learned 📊
- **`ORCHESTRATION_IMPROVEMENTS.md`** — Performance tuning & scaling strategies ⚙️
- **`OPERATIONAL_CHALLENGES.md`** — Real-world troubleshooting & solutions 🐛

### 📚 [reference/](reference/) - Reference Materials
Quick lookups and navigation:

- **`INDEX.md`** — Visual navigation hub with quick links 🗺️
- **`FOLDER_STRUCTURE.md`** — Understanding how this repo is organized 📁

## 🎯 Quick Navigation by Goal

**I want to...**

- ✅ **Deploy on local K8s** → [deployment-guides/self-managed/QUICKSTART.md](deployment-guides/self-managed/QUICKSTART.md)
- ☁️ **Deploy on Azure AKS** → [deployment-guides/aks/AKS_AIRFLOW_DEPLOYMENT_GUIDE.md](deployment-guides/aks/AKS_AIRFLOW_DEPLOYMENT_GUIDE.md)
- 🌟 **Use managed Airflow** → [deployment-guides/astronomer/astronomer.md](deployment-guides/astronomer/astronomer.md)
- 📖 **Learn Airflow from scratch** → [learning/AIRFLOW_BASICS.md](learning/AIRFLOW_BASICS.md)
- 🏗️ **Understand the architecture** → [learning/ARCHITECTURE.md](learning/ARCHITECTURE.md)
- 🔍 **Find a specific topic** → [reference/INDEX.md](reference/INDEX.md)
- 📁 **Navigate the codebase** → [reference/FOLDER_STRUCTURE.md](reference/FOLDER_STRUCTURE.md)
- 🔐 **Secure my deployment** → [deployment-guides/self-managed/SECRETS_MANAGEMENT.md](deployment-guides/self-managed/SECRETS_MANAGEMENT.md)
- 💾 **Query the database** → [deployment-guides/self-managed/POSTGRES_VSCODE_CONNECTION.md](deployment-guides/self-managed/POSTGRES_VSCODE_CONNECTION.md)
- 🏢 **Plan enterprise deployment** → [enterprise/ENTERPRISE_ARCHITECTURE.md](enterprise/ENTERPRISE_ARCHITECTURE.md)
- 🐛 **Fix production issues** → [enterprise/OPERATIONAL_CHALLENGES.md](enterprise/OPERATIONAL_CHALLENGES.md)

## 💡 Pro Tips for Success

> **Working with a team?** Share [00_START_HERE.md](00_START_HERE.md) for smooth onboarding—it creates a personalized path for each role (developer, architect, DevOps).

> **Planning production?** Read in this order: ARCHITECTURE → ENTERPRISE_ARCHITECTURE → SECRETS_MANAGEMENT → AKS_AIRFLOW_DEPLOYMENT_GUIDE

> **Debugging DAGs?** Use [POSTGRES_VSCODE_CONNECTION.md](POSTGRES_VSCODE_CONNECTION.md) to directly query the metadata database and see what Airflow is doing behind the scenes.

## 💡 Pro Tips for Success

> **Working with a team?** Share [00_START_HERE.md](00_START_HERE.md) for smooth onboarding—it creates a personalized path for each role (developer, architect, DevOps).

> **Planning production?** Read in this order: learning/ARCHITECTURE → enterprise/ENTERPRISE_ARCHITECTURE → deployment-guides/self-managed/SECRETS_MANAGEMENT → deployment-guides/aks/AKS_AIRFLOW_DEPLOYMENT_GUIDE

> **Debugging DAGs?** Use [deployment-guides/self-managed/POSTGRES_VSCODE_CONNECTION.md](deployment-guides/self-managed/POSTGRES_VSCODE_CONNECTION.md) to directly query the metadata database and see what Airflow is doing behind the scenes.

## 🆘 Stuck or Need Help?

Follow this troubleshooting path:

1️⃣ **Start with basics** → Check [00_START_HERE.md](00_START_HERE.md) to ensure you're on the right track  
2️⃣ **Deployment issues?** → [deployment-guides/self-managed/QUICKSTART.md](deployment-guides/self-managed/QUICKSTART.md) has troubleshooting sections  
3️⃣ **Concept confusion?** → [learning/AIRFLOW_BASICS.md](learning/AIRFLOW_BASICS.md) explains core ideas  
4️⃣ **Production problems?** → [enterprise/OPERATIONAL_CHALLENGES.md](enterprise/OPERATIONAL_CHALLENGES.md) has real-world solutions  
5️⃣ **Still stuck?** → Check [reference/INDEX.md](reference/INDEX.md) to find the specific guide you need

## 📝 About This Repository

The **root `README.md`** in the main repository provides a high-level overview of the entire project structure. This `docs/README.md` is your hub for all learning and deployment documentation.

---

**Happy Orchestrating! 🎉** Every expert was once a beginner. Take it one step at a time, and don't hesitate to revisit guides as you level up!