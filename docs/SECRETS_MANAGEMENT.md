# 🔐 Secrets Management Guide

Security matters! This guide shows you how to properly manage passwords, API keys, and connection credentials for your Airflow deployment. 🔒

> **⚠️ Golden Rule:** Never commit secrets to Git. Never share them in Slack. Always use proper secret management!

## 📝 Table of Contents
- [Quick Start](#quick-start)
- [Development Setup](#development-setup)
- [Production Setup](#production-setup)
- [Encrypted Secrets Options](#encrypted-secrets-options)
- [Managing Connections](#managing-connections)
- [Best Practices](#best-practices)

---

## Quick Start

### 1. Create Your Local Environment File

```powershell
# Copy the template
Copy-Item .env.example .env

# Edit .env with your actual credentials (never commit this file!)
notepad .env
```

### 2. Create Kubernetes Secrets from .env

```powershell
# Create secrets from your .env file
kubectl create secret generic airflow-secrets -n airflow `
  --from-env-file=.env `
  --dry-run=client -o yaml > kubernetes/secrets-local.yaml

# Apply the secrets
kubectl apply -f kubernetes/secrets-local.yaml

# Or apply the template directly (after editing values)
kubectl apply -f kubernetes/secrets.yaml
```

### 3. Verify Secrets

```powershell
# List all secrets in airflow namespace
kubectl get secrets -n airflow

# View a specific secret (base64 encoded)
kubectl get secret airflow-connections -n airflow -o yaml

# Decode a secret value
kubectl get secret airflow-connections -n airflow -o jsonpath='{.data.AIRFLOW_CONN_ONPREM_DB}' | %{[System.Text.Encoding]::UTF8.GetString([System.Convert]::FromBase64String($_))}
```

---

## Development Setup

### Using Kubernetes Secrets (Recommended for Local Dev)

1. **Edit the secrets template:**
   ```powershell
   notepad kubernetes\secrets.yaml
   ```

2. **Replace all `CHANGE_ME_*` placeholders with your actual values**

3. **Apply secrets:**
   ```powershell
   kubectl apply -f kubernetes/secrets.yaml
   ```

4. **Helm will automatically inject these as environment variables** in Airflow pods

### Using .env File for Quick Testing

For quick local testing without Kubernetes secrets:

```powershell
# Create .env from template
Copy-Item .env.example .env

# Edit with your values
notepad .env

# Create secret from file
kubectl create secret generic airflow-env -n airflow --from-env-file=.env

# Reference in helm-values.yaml:
# env:
#   - secretRef:
#       name: airflow-env
```

---

## Production Setup

**🚨 IMPORTANT:** For production, **NEVER** store secrets in plain YAML files or commit them to Git.

### Option 1: Azure Key Vault + CSI Driver (Recommended for Azure)

1. **Install the Secrets Store CSI Driver:**
   ```powershell
   helm repo add secrets-store-csi-driver https://kubernetes-sigs.github.io/secrets-store-csi-driver/charts
   helm install csi-secrets-store secrets-store-csi-driver/secrets-store-csi-driver -n kube-system
   ```

2. **Install Azure Key Vault Provider:**
   ```powershell
   helm repo add csi-secrets-store-provider-azure https://azure.github.io/secrets-store-csi-driver-provider-azure/charts
   helm install csi-azure csi-secrets-store-provider-azure/csi-secrets-store-provider-azure -n kube-system
   ```

3. **Create Azure Key Vault and store secrets:**
   ```powershell
   az keyvault create --name airflow-kv-prod --resource-group airflow-rg --location eastus
   az keyvault secret set --vault-name airflow-kv-prod --name "onprem-db-password" --value "your-password"
   az keyvault secret set --vault-name airflow-kv-prod --name "azure-storage-key" --value "your-key"
   ```

4. **Create SecretProviderClass:**
   ```yaml
   apiVersion: secrets-store.csi.x-k8s.io/v1
   kind: SecretProviderClass
   metadata:
     name: airflow-azure-keyvault
     namespace: airflow
   spec:
     provider: azure
     parameters:
       keyvaultName: "airflow-kv-prod"
       tenantId: "your-tenant-id"
       objects: |
         array:
           - objectName: "onprem-db-password"
             objectType: "secret"
           - objectName: "azure-storage-key"
             objectType: "secret"
   ```

### Option 2: Sealed Secrets (Recommended for GitOps)

Sealed Secrets allow you to encrypt secrets and safely commit them to Git.

1. **Install Sealed Secrets Controller:**
   ```powershell
   kubectl apply -f https://github.com/bitnami-labs/sealed-secrets/releases/download/v0.24.0/controller.yaml
   ```

2. **Install kubeseal CLI:**
   ```powershell
   # Windows (using Chocolatey)
   choco install kubeseal
   
   # Or download from: https://github.com/bitnami-labs/sealed-secrets/releases
   ```

3. **Create and seal your secrets:**
   ```powershell
   # Create a regular secret (don't apply yet)
   kubectl create secret generic airflow-connections -n airflow `
     --from-literal=AIRFLOW_CONN_ONPREM_DB="mssql://user:pass@host:1433/db" `
     --dry-run=client -o yaml > secrets-temp.yaml
   
   # Seal it (encrypted)
   kubeseal -f secrets-temp.yaml -o yaml > kubernetes/sealed-secrets.yaml
   
   # Safe to commit sealed-secrets.yaml to Git!
   git add kubernetes/sealed-secrets.yaml
   
   # Apply sealed secret (controller will decrypt it in cluster)
   kubectl apply -f kubernetes/sealed-secrets.yaml
   
   # Delete temp file
   Remove-Item secrets-temp.yaml
   ```

### Option 3: External Secrets Operator

Works with Azure Key Vault, AWS Secrets Manager, HashiCorp Vault, Google Secret Manager, etc.

1. **Install External Secrets Operator:**
   ```powershell
   helm repo add external-secrets https://charts.external-secrets.io
   helm install external-secrets external-secrets/external-secrets -n external-secrets-system --create-namespace
   ```

2. **Configure Azure Key Vault as provider:**
   ```yaml
   apiVersion: external-secrets.io/v1beta1
   kind: SecretStore
   metadata:
     name: azure-backend
     namespace: airflow
   spec:
     provider:
       azurekv:
         authType: ManagedIdentity
         vaultUrl: "https://airflow-kv-prod.vault.azure.net"
         tenantId: "your-tenant-id"
   ```

3. **Create ExternalSecret:**
   ```yaml
   apiVersion: external-secrets.io/v1beta1
   kind: ExternalSecret
   metadata:
     name: airflow-connections
     namespace: airflow
   spec:
     refreshInterval: 1h
     secretStoreRef:
       name: azure-backend
       kind: SecretStore
     target:
       name: airflow-connections
       creationPolicy: Owner
     data:
       - secretKey: AIRFLOW_CONN_ONPREM_DB
         remoteRef:
           key: onprem-db-connection-string
   ```

---

## Managing Connections

### Method 1: Kubernetes Secrets (Recommended)

Store connections as environment variables in secrets:

```yaml
# kubernetes/secrets.yaml
apiVersion: v1
kind: Secret
metadata:
  name: airflow-connections
  namespace: airflow
type: Opaque
stringData:
  # Connection URI format: <type>://<user>:<password>@<host>:<port>/<database>?<params>
  AIRFLOW_CONN_ONPREM_DB: "mssql://user:password@server.com:1433/sales_db"
  AIRFLOW_CONN_AZURE_DEFAULT: "wasb://?connection_string=..."
  AIRFLOW_CONN_DATABRICKS_DEFAULT: "databricks://host?token=dapi123..."
```

Airflow automatically picks up connections from `AIRFLOW_CONN_*` environment variables.

### Method 2: Airflow UI (Good for POC/Testing)

1. Navigate to: **Admin → Connections**
2. Click **+** to add a new connection
3. Fill in details:
   - **Conn Id**: `onprem_db`
   - **Conn Type**: `Microsoft SQL Server`
   - **Host**: `on-prem-server.company.com`
   - **Schema**: `sales_db`
   - **Login**: `your_username`
   - **Password**: `your_password`
   - **Port**: `1433`

### Method 3: CLI (Scriptable)

```powershell
# Create connection via CLI
kubectl exec -n airflow deploy/airflow-webserver -- airflow connections add onprem_db `
  --conn-type mssql `
  --conn-host on-prem-server.company.com `
  --conn-login 'db_user' `
  --conn-password 'db_password' `
  --conn-port 1433 `
  --conn-schema 'sales_db'

# Export connections
kubectl exec -n airflow deploy/airflow-webserver -- airflow connections export connections.json

# Import connections
kubectl exec -n airflow deploy/airflow-webserver -- airflow connections import connections.json
```

### Method 4: Backend Secrets (Production)

Configure Airflow to read connections from a secrets backend:

```yaml
# helm-values.yaml
config:
  secrets:
    backend: airflow.providers.hashicorp.secrets.vault.VaultBackend
    backend_kwargs: '{"url": "https://vault.example.com", "token": "..."}'
```

Supported backends:
- HashiCorp Vault
- AWS Systems Manager Parameter Store
- AWS Secrets Manager
- Google Cloud Secret Manager
- Azure Key Vault (via custom provider)

---

## Best Practices

### ✅ DO

1. **Use Kubernetes Secrets** for all passwords and API keys
2. **Encrypt secrets at rest** (enable encryption in Kubernetes or use external KMS)
3. **Use Sealed Secrets or External Secrets Operator** for GitOps workflows
4. **Rotate credentials regularly** (automate with external secrets sync)
5. **Use separate secrets per environment** (dev, staging, prod)
6. **Enable RBAC** to restrict who can read secrets
7. **Audit secret access** using Kubernetes audit logs
8. **Use managed identities** when possible (Azure AD, AWS IAM, GCP Workload Identity)

### ❌ DON'T

1. **Never commit `.env` files** to Git
2. **Never hardcode passwords** in YAML manifests
3. **Never store secrets in ConfigMaps** (they're not encrypted)
4. **Never log or print secrets** in DAG code
5. **Avoid storing secrets in Docker images**
6. **Don't share secrets across namespaces** without proper isolation

---

## Rotation and Maintenance

### Rotate a Secret

```powershell
# Edit the secret
kubectl edit secret airflow-connections -n airflow

# Or recreate it
kubectl delete secret airflow-connections -n airflow
kubectl apply -f kubernetes/secrets.yaml

# Restart pods to pick up new secrets
kubectl rollout restart deployment/airflow-webserver -n airflow
kubectl rollout restart deployment/airflow-scheduler -n airflow
kubectl rollout restart statefulset/airflow-worker -n airflow
```

### Backup Secrets

```powershell
# Export all secrets (be careful with these files!)
kubectl get secrets -n airflow -o yaml > secrets-backup.yaml

# Encrypt the backup
# Windows: Use 7-Zip with AES-256
7z a -p -mhe=on secrets-backup.7z secrets-backup.yaml

# Store in a secure location (Azure Key Vault, password manager, etc.)
```

---

## Troubleshooting

### Secret not found

```powershell
# Check if secret exists
kubectl get secret airflow-connections -n airflow

# Describe for events
kubectl describe secret airflow-connections -n airflow
```

### Connection not working

```powershell
# Test connection from pod
kubectl exec -n airflow deploy/airflow-scheduler -- airflow connections test onprem_db

# Check environment variables in pod
kubectl exec -n airflow deploy/airflow-scheduler -- env | grep AIRFLOW_CONN
```

### Sealed Secret not decrypting

```powershell
# Check controller logs
kubectl logs -n kube-system -l name=sealed-secrets-controller

# Verify certificate
kubeseal --fetch-cert
```

---

## Quick Reference

### Create Secret from Literal Values

```powershell
kubectl create secret generic airflow-connections -n airflow `
  --from-literal=AIRFLOW_CONN_ONPREM_DB='mssql://user:pass@host:1433/db' `
  --from-literal=AIRFLOW_CONN_AZURE_DEFAULT='wasb://...'
```

### Create Secret from File

```powershell
kubectl create secret generic airflow-connections -n airflow `
  --from-env-file=.env
```

### Update Existing Secret

```powershell
kubectl create secret generic airflow-connections -n airflow `
  --from-literal=AIRFLOW_CONN_ONPREM_DB='new-value' `
  --dry-run=client -o yaml | kubectl apply -f -
```

### Delete Secret

```powershell
kubectl delete secret airflow-connections -n airflow
```

---

## Additional Resources

- [Kubernetes Secrets Documentation](https://kubernetes.io/docs/concepts/configuration/secret/)
- [Airflow Connections Documentation](https://airflow.apache.org/docs/apache-airflow/stable/howto/connection.html)
- [Sealed Secrets GitHub](https://github.com/bitnami-labs/sealed-secrets)
- [External Secrets Operator](https://external-secrets.io/)
- [Azure Key Vault CSI Driver](https://azure.github.io/secrets-store-csi-driver-provider-azure/)

---

For help or questions, refer to `docs/SETUP_SUMMARY.md` or raise an issue in the repository.
