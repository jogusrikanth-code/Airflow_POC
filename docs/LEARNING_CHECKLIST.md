# ✅ Learning Checklist - From Airflow Basics to Mastery!

Track your Airflow journey! Check off items as you complete them and celebrate your progress. 🎉

> **💡 How to use this:** Work through phases sequentially. Don't skip ahead—each phase builds on the previous one!

> **🏆 Celebration Tip:** Treat yourself after completing each phase. You're building valuable skills!

---

## 🌟 Phase 1: Understanding Basics (Week 1)

### Core Concepts
- [ ] Read README.md
- [ ] Read AIRFLOW_BASICS.md (complete)
- [ ] Understand DAG concept and why it matters
- [ ] Know the difference between DAG and Task
- [ ] Understand Task dependencies

### Your First DAG
- [ ] Initialize Airflow database (`airflow db init`)
- [ ] Create admin user
- [ ] Start scheduler in one terminal
- [ ] Start webserver in another terminal
- [ ] Access Airflow UI at http://localhost:8080
- [ ] Find `demo_dag` in the UI
- [ ] Enable `demo_dag`
- [ ] Trigger `demo_dag` manually
- [ ] View the DAG run
- [ ] Click on tasks and read logs

### Hands-On: Modify demo_dag.py
- [ ] Add a 3rd task to `demo_dag`
- [ ] Create a new dependency pattern (parallel, diamond, etc.)
- [ ] Run it and verify in UI
- [ ] Check logs to understand execution

### Understanding Operators
- [ ] Know what EmptyOperator does
- [ ] Know what PythonOperator does
- [ ] Know what BashOperator does
- [ ] Understand operator parameters

---

## 🔄 Phase 2: ETL Pipelines (Week 2)

### Study ETL Example
- [ ] Read `etl_example_dag.py` carefully
- [ ] Read extract logic in `src/extract/extract_from_source_a.py`
- [ ] Read transform logic in `src/transform/transform_sales_data.py`
- [ ] Read load logic in `src/load/load_to_dw.py`
- [ ] Understand data flow: raw → processed

### Run ETL Pipeline
- [ ] Enable `etl_example_dag`
- [ ] Trigger it
- [ ] Check input file: `data/raw/sample_source_a.csv`
- [ ] Check output file: `data/processed/sales_daily_summary.csv`
- [ ] Understand the transformation (grouping by date)
- [ ] Read task logs for each step

### Hands-On: Modify Extract Task
- [ ] Change the CSV file being read
- [ ] Add additional logging output
- [ ] Run and verify in UI

### Hands-On: Modify Transform Task
- [ ] Change aggregation (e.g., sum by week instead of date)
- [ ] Add a new calculated column
- [ ] Run and check output file

### Hands-On: Create Own ETL Pipeline
- [ ] Create new DAG: `my_etl_dag.py`
- [ ] Create extract, transform, load tasks
- [ ] Use sample data or create your own
- [ ] Run and verify in UI

---

## 🛠️ Phase 3: Advanced Features (Week 3)

### Task Communication (XCom)
- [ ] Understand XCom purpose
- [ ] Create a DAG with xcom_push()
- [ ] Create a task that xcom_pull() from previous task
- [ ] Verify data passes between tasks

### Scheduling
- [ ] Understand `schedule_interval` parameter
- [ ] Change `demo_dag` to hourly schedule
- [ ] Understand cron syntax: `0 8 * * *`
- [ ] Create DAG with custom cron schedule
- [ ] Test with `airflow dags trigger`

### Error Handling
- [ ] Add retries to a task
- [ ] Add retry_delay
- [ ] Deliberately fail a task and watch it retry
- [ ] Use on_failure callbacks

### Conditional Tasks
- [ ] Study BranchPythonOperator
- [ ] Create DAG with branching logic
- [ ] Test different branch paths

---

## 🧪 Phase 4: Testing (Week 4)

### Unit Testing
- [ ] Create `tests/` directory structure
- [ ] Write test for extract function
- [ ] Write test for transform function
- [ ] Run tests: `pytest tests/`
- [ ] Ensure tests pass

### DAG Validation
- [ ] Run: `airflow dags validate`
- [ ] Run: `airflow dags list`
- [ ] Run: `airflow tasks list -d etl_example_dag`

### Manual Testing
- [ ] Test extract task in isolation: `airflow tasks test demo_dag start 2024-01-01`
- [ ] Test transform task in isolation
- [ ] Test full pipeline

---

## 📚 Phase 5: Organization (Week 5)

### Project Structure
- [ ] Read FOLDER_STRUCTURE.md
- [ ] Review your current folder organization
- [ ] Create additional folders as needed (plugins, config, etc.)
- [ ] Organize DAGs by category if you have many

### Documentation
- [ ] Add docstrings to all DAGs
- [ ] Add docstrings to all task functions
- [ ] Create `docs/architecture.md`
- [ ] Document your data flow

### Version Control
- [ ] Initialize git: `git init`
- [ ] Create `.gitignore`
- [ ] Commit DAG files
- [ ] Commit src/ code
- [ ] Commit tests

---

## 🚀 Phase 6: Production Readiness (Week 6+)

### Monitoring & Alerts
- [ ] Understand task states (running, success, failed, etc.)
- [ ] Set email alerts on task failure
- [ ] Monitor DAG runs in UI
- [ ] Check logs regularly

### Performance Tuning
- [ ] Understand parallelism settings
- [ ] Optimize slow-running tasks
- [ ] Use task pools for resource management

### Security
- [ ] Store credentials in Airflow Connections (not hardcoded)
- [ ] Use Airflow Variables for configuration
- [ ] Secure database access

### Custom Extensions
- [ ] Create custom operator in `plugins/operators/`
- [ ] Create custom hook in `plugins/hooks/`
- [ ] Use in a DAG

### Docker Deployment
- [ ] Understand `docker/docker-compose.yaml`
- [ ] Run: `docker-compose up`
- [ ] Access Airflow from Docker container
- [ ] Deploy as container

---

## 🎓 Knowledge Assessment

### Can You Explain?
- [ ] What is a DAG and why it's important?
- [ ] Difference between DAG and Task
- [ ] How task dependencies work
- [ ] What operators are and give 3 examples
- [ ] How scheduling works
- [ ] The difference between LocalExecutor and SequentialExecutor
- [ ] How to use XCom for task communication
- [ ] Best practices for task design

### Can You Build?
- [ ] A simple 3-task DAG from scratch
- [ ] A complete ETL pipeline
- [ ] A DAG with branching logic
- [ ] A DAG with error handling and retries
- [ ] Tests for your task functions
- [ ] A custom operator

---

## 🏆 Advanced Topics (Optional)

- [ ] Dynamic DAG generation
- [ ] Sensors and external triggers
- [ ] SubDAGs for organization
- [ ] TaskFlow API (modern approach)
- [ ] Kubernetes Executor
- [ ] Celery Executor (distributed)
- [ ] Airflow REST API
- [ ] Custom authentication backends

---

## 📈 Your Learning Journey

### Beginner → Intermediate (3-4 weeks)
- [ ] Phases 1-3 complete
- [ ] Can create and manage basic DAGs
- [ ] Can build simple ETL pipelines
- [ ] Ready for small projects

### Intermediate → Advanced (1-2 months)
- [ ] Phases 4-6 complete
- [ ] Can optimize and monitor DAGs
- [ ] Can build complex workflows
- [ ] Ready for team projects

### Advanced → Expert (3-6 months)
- [ ] Optional topics explored
- [ ] Custom extensions built
- [ ] Production deployments
- [ ] Best practices mastered

---

## 🎯 Milestones

```
Week 1 ✓ Phases 1-2: Understand basics and run first DAG
Week 2 ✓ Phases 2-3: Build your own ETL and learn advanced features
Week 3 ✓ Phase 4: Write tests and validate DAGs
Week 4 ✓ Phase 5: Organize project and use version control
Week 5+ ✓ Phase 6: Deploy to production and optimize
```

---

## 💾 Resources to Revisit

As you progress, refer back to:
- **AIRFLOW_BASICS.md** - For concepts
- **QUICKSTART.md** - For CLI commands
- **FOLDER_STRUCTURE.md** - For organization
- **Official Docs** - https://airflow.apache.org/docs/

---

## 📝 Notes for Your Learning

Add your own notes here as you learn:

```
- Key insight about DAGs:
	_______________________________________________

- Something I struggled with:
	_______________________________________________

- Best practice I discovered:
	_______________________________________________

- Resource I found helpful:
	_______________________________________________

- Next thing to learn:
	_______________________________________________
```

---

## ✅ Final Checklist Before Moving to Production

- [ ] All DAGs validated with `airflow dags validate`
- [ ] All tasks have proper error handling
- [ ] Logs are meaningful and help with debugging
- [ ] Database is backed up (if using PostgreSQL)
- [ ] Security: No hardcoded credentials
- [ ] Documentation: All DAGs documented
- [ ] Tests: Unit tests cover main logic
- [ ] Monitoring: Alerts configured for failures
- [ ] Performance: DAGs execute in reasonable time
- [ ] Team review: Code reviewed by peer

---

**Remember:** Learning Airflow is a journey, not a destination! 

Start simple, build incrementally, and don't rush through phases. 
Focus on understanding concepts rather than memorizing syntax.

Good luck! 🚀
