# Archive Folder

This folder contains historical files that are no longer actively used but kept for reference.

## 📦 Contents

### `Airflow.pgsql`
- **What:** SQL queries for Airflow database
- **Status:** Replaced by `airflow_queries.sql` (root folder) which has more complete and better-organized queries
- **Keep because:** Shows early query development and schema references

### `KUBERNETES_CLEANUP_SUMMARY.md`
- **What:** Documentation of Kubernetes manifest modernization effort
- **Status:** Historical record of migration from old to new K8s manifests
- **Keep because:** Useful reference for understanding the evolution of the deployment approach

### `helm-values.yaml`
- **What:** Early Helm chart values configuration
- **Status:** Superseded by `kubernetes/helm-values.yaml` which is more complete
- **Keep because:** Shows initial Helm configuration attempts and decisions

### `replace.txt`
- **What:** Git filter-repo mapping file for secret redaction
- **Status:** Used during attempted Git history cleanup (ultimately not needed)
- **Keep because:** Documents the secret removal approach that was tried

## 🗂️ Why Archive Instead of Delete?

These files provide context about:
- How the project evolved
- Decisions that were made
- Alternative approaches that were tried
- Historical configurations

If you need to understand why something is the way it is now, these archived files can provide valuable context!

---

**Note:** These files are kept in version control but are not actively maintained. For current, production-ready files, refer to the main project directories.
