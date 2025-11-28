# Setup Summary

This project runs Apache Airflow on Kubernetes (Docker Desktop) and demonstrates an end‑to‑end enterprise pipeline. This guide covers how to access the UI, set credentials, and ensure DAGs are visible via either local mounts or Helm + git-sync.

## Airflow UI Access
- Service: `airflow-webserver` (type `LoadBalancer`)
- URL: `http://localhost:8080` (Docker Desktop exposes LoadBalancer at localhost)
- Verify service:
	- PowerShell:
		```powershell
		kubectl get svc airflow-webserver -n airflow -o wide
		```
- If `EXTERNAL-IP` is pending, use port-forward instead:
	```powershell
	$pod = kubectl get pods -n airflow -l app=airflow,component=webserver -o jsonpath="{.items[0].metadata.name}"
	kubectl port-forward -n airflow pod/$pod 8080:8080
	# Open http://localhost:8080
	```

## UI Credentials
- Default admin user may not persist automatically; create/reset via pod:
	```powershell
	$pod = (kubectl get pods -n airflow | Select-String "airflow-webserver" | ForEach-Object { ($_ -split "\s+")[0] } | Select-Object -First 1)
	# Create admin user (change password as needed)
	kubectl exec -it -n airflow $pod -- airflow users create --username admin --password "<YourStrongPass>" --firstname Admin --lastname Admin --role Admin --email admin@example.com
	# Or reset existing admin password
	kubectl exec -it -n airflow $pod -- airflow users set-password -u admin -p "<YourStrongPass>"
	```

## Mount Local DAGs, Plugins, and src
Airflow must see your repository’s `dags/`, `plugins/`, and Python package `src/` inside the containers. This repo uses hostPath mounts in `kubernetes/airflow.yaml` that point to the Docker Desktop Linux VM path for your Windows folders.

- Paths used (adjust for your Windows username/path):
	- `dags` → `/run/desktop/mnt/host/c/Users/sjogu/OneDrive - Spencer Gifts LLC/Documents/Srikanth_Jogu/Airflow_POC/dags`
	- `src` → `/run/desktop/mnt/host/c/Users/sjogu/OneDrive - Spencer Gifts LLC/Documents/Srikanth_Jogu/Airflow_POC/src` (mounted at `/opt/airflow/dags/src`)
	- `plugins` → `/run/desktop/mnt/host/c/Users/sjogu/OneDrive - Spencer Gifts LLC/Documents/Srikanth_Jogu/Airflow_POC/plugins`

- Why mount `src` under `dags/`: Airflow adds the DAG folder to `PYTHONPATH`, so `from src...` imports work during DAG parsing.

- Apply manifests:
	```powershell
	kubectl apply -f kubernetes/airflow.yaml
	# If you see immutable selector errors on webserver, recreate it:
	kubectl delete deploy airflow-webserver -n airflow --ignore-not-found=true
	kubectl apply -f kubernetes/airflow.yaml
	kubectl rollout status deploy/airflow-webserver -n airflow
	```

## Verify DAG Discovery
- List DAGs from the webserver pod:
	```powershell
	$pod = (kubectl get pods -n airflow | Select-String "airflow-webserver-" | ForEach-Object { ($_ -split "\s+")[0] } | Select-Object -First 1)
	kubectl exec -n airflow $pod -- airflow dags list
	kubectl exec -n airflow $pod -- airflow dags list-import-errors
	```
- In the UI, unpause `enterprise_integration_pipeline` to run it.

## Troubleshooting
- No DAGs in UI:
	- Confirm mounts with `kubectl exec` and `ls -la /opt/airflow/dags`.
	- Ensure the hostPath paths point to your actual repo location (update `kubernetes/airflow.yaml` if your Windows path differs).
	- Check import errors: `airflow dags list-import-errors`.
- Can’t log in:
	- Create/Reset admin user as shown above.
	- Confirm you’re accessing the correct service/port.
- Scheduler/Worker issues:
	- Check pods: `kubectl get pods -n airflow -o wide`.
	- View logs: `kubectl logs -n airflow <pod-name>`.

## Helm + Git Sync (Recommended)
Use the Helm chart’s `git-sync` sidecars to pull DAGs from your Git repository into every Airflow component (scheduler, workers, webserver, etc.). This avoids machine‑specific host paths and keeps everything in sync.

1) Ensure `kubernetes/helm-values.yaml` has git-sync configured:
	- `dags.gitSync.enabled: true`
	- `dags.gitSync.repo: https://github.com/<org>/<repo>.git`
	- `dags.gitSync.subPath: "."` (sync whole repo so `src/` imports work)
	- `dags.gitSync.credentialsSecret: git-credentials`

2) Create a GitHub Personal Access Token (classic) with `repo` (read) scope and a Kubernetes secret (git-sync v4 keys):
	```powershell
	kubectl create secret generic git-credentials -n airflow `
	  --from-literal=GITSYNC_USERNAME='<your_github_username>' `
	  --from-literal=GITSYNC_PASSWORD='<your_github_pat>'
	```

3) Deploy/upgrade Airflow via Helm:
	```powershell
	helm repo add apache-airflow https://airflow.apache.org
	helm repo update
	helm upgrade --install airflow apache-airflow/airflow -n airflow -f kubernetes/helm-values.yaml
	```

4) Verify DAGs and access UI:
	```powershell
	kubectl get pods -n airflow
	kubectl get svc -n airflow
	kubectl port-forward -n airflow svc/airflow-webserver 8080:8080
	# Open http://localhost:8080 and login with admin / your password
	```

## Alternative: hostPath (Local Dev)
If you prefer mounting local folders directly, use the provided `kubernetes/airflow.yaml` which mounts `dags/`, `plugins/`, and `src/` from the Docker Desktop VM path.

For production or collaborative teams, prefer Git Sync or a custom image to avoid machine‑specific paths.
