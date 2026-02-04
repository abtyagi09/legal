# 🚀 Quick Deployment - Legal Document Agent

## One-Command Deployment

```powershell
# Deploy everything to Azure
azd up
```

That's it! This single command will:
- ✅ Create all Azure resources
- ✅ Build Docker image
- ✅ Deploy to Container Apps
- ✅ Configure managed identity
- ✅ Set up monitoring

## Prerequisites (One-time setup)

```powershell
# 1. Install Azure Developer CLI
winget install microsoft.azd

# 2. Login to Azure
azd auth login

# 3. Have a Microsoft Foundry model deployed
# Visit: https://ai.azure.com
```

## Step-by-Step First Deployment

```powershell
# 1. Navigate to project
cd c:\agents\legal

# 2. Run the deployment script
.\deploy.ps1

# Or manually:
azd init
azd env set FOUNDRY_ENDPOINT "https://your-project.api.azureml.ms"
azd env set FOUNDRY_MODEL_DEPLOYMENT "gpt-5"
azd up
```

## What Gets Deployed

| Service | Purpose | Monthly Cost |
|---------|---------|--------------|
| Container Apps | Host the agent | ~$73 |
| Azure AI Search | Document search | ~$250 |
| Document Intelligence | Document analysis | Pay-per-use |
| Container Registry | Store images | ~$5 |
| Key Vault | Store secrets | ~$3 |
| Monitoring | Logs & metrics | ~$10-50 |

**Total: ~$341-391/month** (plus Foundry model usage)

## Common Commands

```powershell
# Full deployment
azd up

# Just provision resources
azd provision

# Just deploy code
azd deploy

# View deployed resources
azd show

# Stream logs
azd monitor

# Delete everything
azd down
```

## After Deployment

1. **Create Search Index**
   ```powershell
   # Use the provided schema
   az search index create --service-name <name> --name legal-documents-index --fields @search-index-schema.json
   ```

2. **Upload Documents**
   - Use Azure Portal or SDK to upload legal documents to the search index

3. **Test Application**
   ```powershell
   # Get URL
   $url = azd env get-value AZURE_CONTAINER_APP_URL
   Write-Host "App URL: $url"
   ```

## Troubleshooting

**Issue**: azd command not found  
**Fix**: `winget install microsoft.azd`

**Issue**: Deployment failed  
**Fix**: Run `azd up --debug` to see detailed errors

**Issue**: Container not starting  
**Fix**: Check logs with `azd monitor` or view in Azure Portal

## Multiple Environments

```powershell
# Create dev environment
azd env new legal-agent-dev
azd up

# Create prod environment  
azd env new legal-agent-prod
azd up

# Switch environments
azd env select legal-agent-dev
```

## Cost Management

```powershell
# Scale down for dev
az containerapp update --min-replicas 0 --max-replicas 1 ...

# Delete when not needed
azd down
```

## Full Documentation

- **Quick Start**: See [QUICKSTART.md](QUICKSTART.md)
- **azd Details**: See [AZD_DEPLOYMENT.md](AZD_DEPLOYMENT.md)
- **Manual Deployment**: See [DEPLOYMENT.md](DEPLOYMENT.md)
- **Architecture**: See [PROJECT_SUMMARY.md](PROJECT_SUMMARY.md)

---

**Ready?** Run: `.\deploy.ps1` or `azd up`
