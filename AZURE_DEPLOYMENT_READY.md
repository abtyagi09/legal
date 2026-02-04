# ✅ Azure Deployment Ready - Legal Document Agent

## 🎉 What's Been Set Up

Your Legal Document Agent is now ready for **one-command Azure deployment** using Azure Developer CLI (azd)!

### Infrastructure as Code Created

```
c:\agents\legal/
├── azure.yaml                      # azd configuration
├── infra/
│   ├── main.bicep                  # Main infrastructure orchestration
│   ├── main.parameters.json        # Deployment parameters
│   ├── abbreviations.json          # Resource naming conventions
│   └── core/
│       ├── host/
│       │   ├── container-registry.bicep
│       │   ├── container-apps-environment.bicep
│       │   └── container-app.bicep
│       ├── ai/
│       │   ├── search.bicep
│       │   └── documentintelligence.bicep
│       ├── security/
│       │   ├── keyvault.bicep
│       │   ├── keyvault-secrets.bicep
│       │   └── role-assignment.bicep
│       └── monitor/
│           ├── loganalytics.bicep
│           └── applicationinsights.bicep
├── deploy.ps1                      # Interactive deployment script
├── search-index-schema.json        # Azure AI Search index definition
├── AZD_DEPLOYMENT.md              # Complete azd guide
└── QUICK_DEPLOY.md                # One-page quick reference
```

## 🚀 Deploy Now (3 Steps)

### Step 1: Install Azure Developer CLI

```powershell
winget install microsoft.azd
```

### Step 2: Prepare Microsoft Foundry Model

Before deploying, deploy a model in Microsoft Foundry:
1. Visit [ai.azure.com](https://ai.azure.com)
2. Create or select a project
3. Deploy **GPT-5** or **Claude Sonnet 4.5**
4. Copy the endpoint URL and deployment name

### Step 3: Deploy Everything

```powershell
cd c:\agents\legal
.\deploy.ps1
```

Or manually:

```powershell
# Login
azd auth login

# Set Foundry details
azd env set FOUNDRY_ENDPOINT "https://your-project.api.azureml.ms"
azd env set FOUNDRY_MODEL_DEPLOYMENT "gpt-5"

# Deploy everything!
azd up
```

## ✨ What Gets Deployed

The `azd up` command automatically creates:

| Resource | Description | Configuration |
|----------|-------------|---------------|
| **Resource Group** | Container for all resources | Auto-named |
| **Container Registry** | Stores Docker images | Basic tier |
| **Container Apps Environment** | Host environment | With Log Analytics |
| **Container App** | Your agent application | 2 vCPU, 4GB RAM, auto-scale 1-5 |
| **Azure AI Search** | Document search service | Standard tier, semantic search enabled |
| **Document Intelligence** | Document analysis | S0 tier, prebuilt models |
| **Key Vault** | Secret storage | Stores API keys securely |
| **Log Analytics** | Centralized logging | 30-day retention |
| **Application Insights** | App monitoring | Connected to Log Analytics |
| **Managed Identity** | Secure authentication | Auto-configured with RBAC |

**Total deployment time: ~8-15 minutes**

## 🎯 Key Features

### ✅ Infrastructure as Code
- All resources defined in Bicep
- Reproducible deployments
- Version controlled
- Easy to customize

### ✅ Security Best Practices
- Managed Identity (no API keys in code)
- Secrets stored in Key Vault
- RBAC role assignments
- HTTPS ingress only

### ✅ Production Ready
- Auto-scaling (1-5 replicas)
- Health checks configured
- Monitoring and logging
- Container optimization

### ✅ Cost Optimized
- Right-sized resources
- Pay for what you use
- Easy to scale down/up
- Clear cost breakdown

## 📊 Azure Resources Created

```
┌─────────────────────────────────────┐
│     Resource Group                  │
│     rg-legal-agent-{uniqueid}      │
├─────────────────────────────────────┤
│                                     │
│  📦 Container Registry              │
│     cr{uniqueid}                    │
│                                     │
│  🚀 Container Apps Environment      │
│     cae-{uniqueid}                  │
│     └─ Container App                │
│        ca-{uniqueid}                │
│        • legal-document-agent:latest│
│        • Managed Identity           │
│                                     │
│  🔍 Azure AI Search                 │
│     srch-{uniqueid}                 │
│     • Standard tier                 │
│     • Semantic search enabled       │
│                                     │
│  📄 Document Intelligence           │
│     cog-{uniqueid}                  │
│     • S0 tier                       │
│                                     │
│  🔐 Key Vault                       │
│     kv-{uniqueid}                   │
│     • Secrets: search-api-key       │
│     • Secrets: doc-intel-key        │
│                                     │
│  📊 Log Analytics                   │
│     log-{uniqueid}                  │
│                                     │
│  📈 Application Insights            │
│     appi-{uniqueid}                 │
│                                     │
└─────────────────────────────────────┘
```

## 🔧 Post-Deployment Steps

### 1. Create Search Index

```powershell
$searchName = azd env get-value AZURE_SEARCH_NAME
az search index create `
  --service-name $searchName `
  --name "legal-documents-index" `
  --fields '@search-index-schema.json'
```

### 2. Test Deployment

```powershell
# Get application URL
$appUrl = azd env get-value AZURE_CONTAINER_APP_URL
Write-Host "App URL: $appUrl"

# View logs
azd monitor
```

### 3. Upload Documents

Use Azure Portal or SDK to upload legal documents to your search index.

## 💰 Cost Estimate

| Service | Tier | Monthly Cost |
|---------|------|--------------|
| Container Apps (2 vCPU, 4GB) | Standard | $73 |
| Azure AI Search | Standard | $250 |
| Document Intelligence | S0 | Pay-per-use (~$1-50) |
| Container Registry | Basic | $5 |
| Key Vault | Standard | $3 |
| Log Analytics | Pay-as-you-go | $10-50 |
| **Subtotal** | | **$342-431/month** |
| Microsoft Foundry (GPT-5) | Pay-per-token | Varies by usage |

### Cost Optimization Tips

```powershell
# Scale to zero during off-hours
az containerapp update --min-replicas 0 --max-replicas 3 ...

# Use Basic search tier for dev
# Edit infra/main.bicep and change sku to 'basic'

# Delete when not needed
azd down
```

## 📖 Documentation Overview

| Document | Purpose |
|----------|---------|
| **[QUICK_DEPLOY.md](QUICK_DEPLOY.md)** | One-page deployment reference |
| **[AZD_DEPLOYMENT.md](AZD_DEPLOYMENT.md)** | Complete azd guide with troubleshooting |
| **[DEPLOYMENT.md](DEPLOYMENT.md)** | Manual deployment (Azure CLI/Portal) |
| **[QUICKSTART.md](QUICKSTART.md)** | Local development setup |
| **[README.md](README.md)** | Full feature documentation |
| **[PROJECT_SUMMARY.md](PROJECT_SUMMARY.md)** | Technical architecture |

## 🎓 Common Commands Reference

```powershell
# Deploy everything
azd up

# Just provision resources
azd provision

# Just deploy code
azd deploy

# View resources
azd show

# Get environment variables
azd env get-values

# Stream logs
azd monitor

# Delete everything
azd down

# Multiple environments
azd env new legal-agent-prod
azd env select legal-agent-prod
```

## 🔍 Monitoring & Management

### View Logs
```powershell
# Live logs
az containerapp logs show `
  --name $(azd env get-value AZURE_CONTAINER_APP_NAME) `
  --resource-group $(azd env get-value AZURE_RESOURCE_GROUP) `
  --follow
```

### Scale Application
```powershell
az containerapp update `
  --name $(azd env get-value AZURE_CONTAINER_APP_NAME) `
  --resource-group $(azd env get-value AZURE_RESOURCE_GROUP) `
  --min-replicas 2 `
  --max-replicas 10
```

### Update Configuration
```powershell
# Change model
azd env set FOUNDRY_MODEL_DEPLOYMENT "claude-sonnet-4-5"
azd deploy
```

## 🛠️ Customization

### Modify Infrastructure

Edit `infra/main.bicep` to:
- Change resource tiers (e.g., Basic search for dev)
- Add VNet integration
- Adjust CPU/memory allocations
- Add custom domains
- Enable private endpoints

### Update Application

Edit code and redeploy:
```powershell
# Make changes to src/ files
azd deploy
```

## 🆘 Troubleshooting

### azd not found
```powershell
winget install microsoft.azd
# Or download from: https://aka.ms/install-azd
```

### Deployment fails
```powershell
# Run with debug
azd up --debug

# Check specific service
az containerapp show --name <name> --resource-group <rg>
```

### App not starting
```powershell
# Check environment variables
azd env get-values

# View logs
azd monitor
```

## 🌟 Next Steps

1. **Deploy**: Run `.\deploy.ps1` or `azd up`
2. **Create Index**: Use `search-index-schema.json`
3. **Upload Docs**: Add legal documents to search
4. **Test**: Try queries via the API or CLI
5. **Monitor**: Check Application Insights
6. **Scale**: Adjust based on usage
7. **Secure**: Enable VNet for production

## 📞 Support

- **azd Issues**: [GitHub Issues](https://github.com/Azure/azure-dev/issues)
- **Azure Support**: [Azure Portal Support](https://portal.azure.com/#blade/Microsoft_Azure_Support/HelpAndSupportBlade)
- **Documentation**: 
  - [Azure Container Apps](https://learn.microsoft.com/azure/container-apps)
  - [Azure Developer CLI](https://learn.microsoft.com/azure/developer/azure-developer-cli)
  - [Microsoft Agent Framework](https://github.com/microsoft/agent-framework)

---

## ✅ Ready to Deploy!

Everything is configured. Just run:

```powershell
cd c:\agents\legal
.\deploy.ps1
```

**Estimated time**: 10-15 minutes for first deployment

**Result**: Fully functional AI agent running in Azure with all required services!

🎉 **Happy Deploying!**
