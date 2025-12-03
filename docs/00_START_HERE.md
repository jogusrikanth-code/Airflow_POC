# 🚀 Welcome to Your Airflow POC Journey!

**Hey there!** 👋 Glad you're here! This is your starting point for everything Airflow.

---

## 🗺️ Your Learning Path

Think of this as your GPS through Airflow land. Here's the route I recommend:

### Step 1️⃣: Understand the Big Picture
📖 **Read:** [`ARCHITECTURE.md`](./ARCHITECTURE.md)
- Get a visual overview of how everything fits together
- Understand the flow from code to execution
- See the Kubernetes components in action

**Time:** 15 minutes | **Difficulty:** 🟢 Beginner-friendly

---

### Step 2️⃣: Get Up and Running
⚡ **Read:** [`QUICKSTART.md`](./QUICKSTART.md)
- Deploy Airflow on Kubernetes in minutes
- Access the web UI
- Run your first DAG

**Time:** 30 minutes | **Difficulty:** 🟢 Easy with copy-paste commands

---

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
