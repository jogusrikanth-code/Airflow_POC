# Finding IP Allowlist Settings in Databricks Workspace

## Your Workspace: https://adb-5444953219183209.9.azuredatabricks.net
## IP to Whitelist: **48.216.148.118**

---

## Method 1: Via Settings Menu (Most Common)

### Step 1: Access Settings
1. Log into: `https://adb-5444953219183209.9.azuredatabricks.net`
2. Look for **Settings** icon (gear icon ⚙️) in the left sidebar OR
3. Click your **profile picture/username** in the top right
4. Select **"Settings"** from the dropdown

### Step 2: Find IP Access List
Look for one of these sections (varies by version):
- **"Security"** → **"Network"** → **"IP Access Lists"**
- **"Workspace Settings"** → **"Security"** → **"IP Access Lists"**
- **"Settings"** → **"Network Access"** → **"IP Access Lists"**
- **"Admin Console"** → **"Access Control"** → **"IP Access Lists"**

### Step 3: Add IP Address
1. Click **"Add"** or **"Edit Access List"**
2. Enter:
   - **IP Address/CIDR**: `48.216.148.118/32` (the `/32` means single IP)
   - **Label/Comment**: `AKS Airflow Cluster`
   - **Type**: Allow (or Whitelist)
3. Click **"Add"** or **"Save"**

---

## Method 2: Via Admin Console (Azure Databricks)

### If you have Azure Databricks:
1. Go to **Azure Portal** (`https://portal.azure.com`)
2. Search for your Databricks workspace: **"adb-5444953219183209"**
3. Click on the workspace
4. In the left menu, look for:
   - **"Networking"**
   - **"Public Network Access"**
   - **"Firewall"**
5. Find **"Add client IP"** or **"Firewall rules"**
6. Add IP: `48.216.148.118`
7. Save changes

---

## Method 3: Via Account Console (Databricks Accounts)

### If you have account-level access:
1. Go to: `https://accounts.cloud.databricks.com/` (or your account URL)
2. Sign in with your credentials
3. Navigate to:
   - **"Workspaces"** → Select your workspace
   - **"Settings"** → **"Network"**
   - **"IP Access Lists"**
4. Add the IP: `48.216.148.118/32`
5. Apply to your workspace

---

## Method 4: Check Current Restrictions

### To see if IP restrictions are active:
1. In your Databricks workspace, go to **Settings** (gear icon)
2. Look for **"Workspace Settings"** or **"Admin Settings"**
3. Check these sections:
   - **Security** → Look for "IP Access List" or "Network Security"
   - **Advanced** → Look for "Network Access Control"
   - **Compliance** → Check for IP restrictions

### Current Status Indicators:
If you see any of these, IP restrictions ARE active:
- ✅ "IP Access Lists: Enabled"
- ✅ "Network Access Control: Enabled"
- ✅ "Public Network Access: Enabled with restrictions"

---

## What the Settings Look Like (Screenshots Reference)

### Typical UI Elements to Look For:

**Left Sidebar**:
```
📊 Workspace
👥 Users & Groups
🔐 Security
   ├── Access Control
   ├── IP Access Lists  ← LOOK HERE
   └── Service Principals
⚙️ Settings
   └── Network Access  ← OR HERE
```

**Settings Page**:
```
Settings
├── General
├── Security
│   ├── Access tokens
│   ├── IP Access Lists  ← HERE
│   └── Service principals
├── Network
│   └── IP Access Lists  ← OR HERE
└── Advanced
```

---

## Alternative: Ask Your Admin to Run This

If you can't find the settings (you might not have admin access), ask your Databricks admin to:

### Option A: Via Databricks CLI
```bash
databricks ip-access-lists create \
  --label "AKS Airflow Cluster" \
  --list-type ALLOW \
  --ip-addresses 48.216.148.118
```

### Option B: Via Databricks API
```bash
curl -X POST https://adb-5444953219183209.9.azuredatabricks.net/api/2.0/ip-access-lists \
  -H "Authorization: Bearer <ADMIN_TOKEN>" \
  -H "Content-Type: application/json" \
  -d '{
    "label": "AKS Airflow Cluster",
    "list_type": "ALLOW",
    "ip_addresses": ["48.216.148.118"]
  }'
```

### Option C: Via Azure ARM Template (if Azure Databricks)
```json
{
  "properties": {
    "publicNetworkAccess": "Enabled",
    "requiredNsgRules": "AllRules",
    "parameters": {
      "enableIpAccessLists": {
        "value": true
      },
      "ipAccessLists": [
        {
          "listType": "Allow",
          "ipAddresses": ["48.216.148.118"],
          "label": "AKS Airflow Cluster"
        }
      ]
    }
  }
}
```

---

## Verify Access After Adding IP

Once the IP is added, test immediately:

```powershell
# Run this from your machine to verify
kubectl exec -n airflow airflow-dag-processor-64598fd9f4-j24sj -c dag-processor -- \
  airflow dags test databricks_list_workflows 2025-12-05
```

**Expected output after whitelisting**:
```
✅ Connection retrieved: databricks_default
✅ WorkspaceClient created successfully
📋 Fetching workflows/jobs from workspace...
======================================================================
WORKFLOWS/JOBS IN WORKSPACE
======================================================================
#1 📌 Job ID: 123
    Name: My Job
✅ Total Workflows Found: 15
```

---

## Troubleshooting: Can't Find IP Access List Settings

### Reason 1: You Don't Have Admin Access
**Solution**: Ask someone with these roles:
- Workspace Admin
- Account Admin
- Azure Subscription Owner/Contributor

### Reason 2: IP Access Lists Not Enabled Yet
**Solution**: It needs to be enabled first:
1. Go to Settings → Security → Advanced
2. Look for "Enable IP Access Lists"
3. Toggle it ON
4. Then you can add IPs

### Reason 3: Azure Managed Network
**Solution**: If using Azure Private Link or VNet injection:
- IP allowlisting might be in **Azure Portal** → **Databricks Workspace** → **Networking**
- Look for "Public network access" settings

### Reason 4: Account-Level Policy
**Solution**: IP restrictions might be set at account level:
- Go to `accounts.cloud.databricks.com`
- Check account-level settings first
- Workspace inherits from account

---

## Alternative Solution: Temporary Workaround

If you can't add the IP immediately, you can:

### Generate a New PAT Token from a Whitelisted Location
1. Access Databricks from your office network (if whitelisted)
2. Go to User Settings → Developer → Access Tokens
3. Generate new token
4. Update Airflow connection with new token

This might work if your office/VPN IP is already whitelisted.

---

## Summary: Information for Your Admin

Please forward this to your Databricks administrator:

**Request**: Add IP to workspace allowlist
**IP Address**: `48.216.148.118/32`
**Purpose**: AKS Airflow cluster integration
**Workspace**: `https://adb-5444953219183209.9.azuredatabricks.net`
**Workspace ID**: `5444953219183209`
**Impact**: Allows Airflow running on AKS to trigger Databricks jobs
**Security**: Single IP, can be revoked anytime

---

## Quick Decision Tree

```
Can you see "Settings" or gear icon (⚙️)?
├─ YES → Go to Settings
│   └─ Do you see "IP Access Lists"?
│       ├─ YES → Add IP: 48.216.148.118/32
│       └─ NO → You don't have admin access
│           └─ Contact: Databricks Admin or Azure Subscription Owner
│
└─ NO → Not logged in or insufficient permissions
    └─ Contact: Databricks Admin
```
