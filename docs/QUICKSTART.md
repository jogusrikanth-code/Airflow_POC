# Quickstart

This guide gets you into the Airflow UI quickly and shows two ways to make DAGs available: hostPath mounts (local dev) and Helm git-sync (team/prod-friendly).

## 1) Apply Kubernetes Manifests (local dev)
- Deploy/update resources:
	```powershell
	kubectl apply -f kubernetes/airflow.yaml
	# If immutable selector error on webserver, recreate and re-apply
	kubectl delete deploy airflow-webserver -n airflow --ignore-not-found=true
	kubectl apply -f kubernetes/airflow.yaml
	kubectl rollout status deploy/airflow-webserver -n airflow
	```
- UI: open `http://localhost:8080`
- Create or reset admin user:
	```powershell
	$pod = (kubectl get pods -n airflow | Select-String "airflow-webserver-" | ForEach-Object { ($_ -split "\s+")[0] } | Select-Object -First 1)
	kubectl exec -it -n airflow $pod -- airflow users create --username admin --password "<YourStrongPass>" --firstname Admin --lastname Admin --role Admin --email admin@example.com
	# or
	kubectl exec -it -n airflow $pod -- airflow users set-password -u admin -p "<YourStrongPass>"
	```
- Unpause the DAG `enterprise_integration_pipeline` in the UI.

Note: The manifests mount your local repo into the pods via Docker Desktop’s Linux VM path. If your Windows path differs, update `kubernetes/airflow.yaml` hostPath entries. See `docs/SETUP_SUMMARY.md` for details.

## 2) Helm with Git Sync (recommended for teams)
Use the official Helm chart and pull DAGs from Git automatically. A sample config is included (commented) in `kubernetes/helm-values.yaml`.

Steps:
1. Install chart repo and deploy with values:
	 ```powershell
	 helm repo add apache-airflow https://airflow.apache.org
	 helm repo update
	 # Edit kubernetes/helm-values.yaml and set/enable dags.gitSync (see below)
	 helm upgrade --install airflow apache-airflow/airflow -n airflow -f kubernetes/helm-values.yaml --create-namespace
	 ```
2. In `kubernetes/helm-values.yaml`, uncomment and set `dags.gitSync` (repo/branch/subPath). Example:
	 ```yaml
	 dags:
		 persistence:
			 enabled: false
		 gitSync:
			 enabled: true
			 repo: "https://github.com/your-org/Airflow_POC.git"
			 branch: "master"
			 subPath: "dags"
			 depth: 1
			 syncWait: 60
	 ```
3. Access the UI at `http://localhost:8080` and create/reset the admin user if necessary (see above).

Troubleshooting:
- No DAGs: verify `airflow dags list` in webserver pod and check `airflow dags list-import-errors`.
- Login issues: recreate/reset the admin user.
- Import errors: ensure any `src/` modules are available (for hostPath setup we mount `src` under the DAGs folder; for git-sync, either vendor `src` into the repo or build a custom image).

