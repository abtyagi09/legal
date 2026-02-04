# Azure Developer CLI (azd) Deployment Guide

This guide walks you through deploying the Legal Document Agent to Azure using Azure Developer CLI (azd).

## Prerequisites

1. **Azure Developer CLI (azd)** - [Install azd](https://learn.microsoft.com/azure/developer/azure-developer-cli/install-azd)
2. **Azure CLI** - [Install Azure CLI](https://learn.microsoft.com/cli/azure/install-azure-cli)
3. **Docker Desktop** - For building container images
4. **Azure Subscription** - With appropriate permissions
5. **Microsoft Foundry Access** - For AI model deployment

## Quick Start

### 1. Initialize azd Environment

```powershell
# Navigate to project directory
cd c:\agents\legal

# Initialize azd (first time only)
azd init
```

When prompted:
- Environment name: `legal-agent-dev` (or your preferred name)
- Subscription: Select your Azure subscription
- Location: Choose a region (e.g., `eastus`, `westus2`)

### 2. Set Up Microsoft Foundry Model

Before deploying, you need a Microsoft Foundry model deployed:

**Option A: Use AI Toolkit in VS Code**
1. Press `Ctrl+Shift+P` and run: `AI Toolkit: Browse Model Catalog`
2. Filter by "Microsoft Foundry"
3. Select **GPT-5** or **Claude Sonnet 4.5**
4. Click "Deploy" and follow prompts
5. Note the endpoint and deployment name

**Option B: Use Azure Portal**
1. Go to [ai.azure.com](https://ai.azure.com)
2. Create or select a project
3. Deploy a model (GPT-5 recommended)
4. Copy the endpoint and deployment name

### 3. Configure Environment Variables

```powershell
# Set your Foundry endpoint
azd env set FOUNDRY_ENDPOINT "https://your-project.api.azureml.ms"

# Set your model deployment name
azd env set FOUNDRY_MODEL_DEPLOYMENT "gpt-5"
```

### 4. Provision Azure Resources

```powershell
# Provision all Azure resources (one command!)
azd provision
```

This will create:
- ✅ Resource Group
- ✅ Azure Container Registry
- ✅ Azure Container Apps Environment
- ✅ Azure AI Search (with semantic search)
- ✅ Azure Document Intelligence
- ✅ Azure Key Vault (for secrets)
- ✅ Log Analytics + Application Insights
- ✅ Managed Identities and Role Assignments

**Provisioning takes ~5-10 minutes**

### 5. Deploy Application

```powershell
# Build and deploy the container app
azd deploy
```

This will:
1. Build the Docker image
2. Push to Azure Container Registry
3. Deploy to Azure Container Apps
4. Configure environment variables
5. Set up managed identity

**Deployment takes ~3-5 minutes**

### 6. Create Search Index

After deployment, create the search index:

```powershell
# Get the search service details
$searchEndpoint = azd env get-value AZURE_SEARCH_ENDPOINT
$searchName = azd env get-value AZURE_SEARCH_NAME

# Get API key from Key Vault
$kvName = azd env get-value AZURE_KEYVAULT_NAME
$searchKey = az keyvault secret show --vault-name $kvName --name search-api-key --query value -o tsv

# Create index using Azure CLI or REST API
az search index create `
  --service-name $searchName `
  --name "legal-documents-index" `
  --fields '@search-index-schema.json'
```

Or create manually in Azure Portal.

### 7. Test Your Deployment

```powershell
# Get the application URL
$appUrl = azd env get-value AZURE_CONTAINER_APP_URL
Write-Host "Application URL: $appUrl" -ForegroundColor Green

# Test the endpoint (if API mode)
curl $appUrl/health
```

## Detailed Commands

### View All Resources

```powershell
# List all provisioned resources
azd show

# Get specific output values
azd env get-values
```

### Update Configuration

```powershell
# Update environment variable
azd env set FOUNDRY_MODEL_DEPLOYMENT "claude-sonnet-4-5"

# Redeploy with new config
azd deploy
```

### View Logs

```powershell
# Stream application logs
az containerapp logs show `
  --name $(azd env get-value AZURE_CONTAINER_APP_NAME) `
  --resource-group $(azd env get-value AZURE_RESOURCE_GROUP) `
  --follow
```

### Scale Application

```powershell
# Scale up/down
az containerapp update `
  --name $(azd env get-value AZURE_CONTAINER_APP_NAME) `
  --resource-group $(azd env get-value AZURE_RESOURCE_GROUP) `
  --min-replicas 2 `
  --max-replicas 10
```

## Environment Management

### Multiple Environments

Deploy to different environments (dev, staging, prod):

```powershell
# Create dev environment
azd env new legal-agent-dev
azd env set FOUNDRY_ENDPOINT "..."
azd provision
azd deploy

# Create prod environment
azd env new legal-agent-prod
azd env set FOUNDRY_ENDPOINT "..."
azd provision
azd deploy

# Switch between environments
azd env select legal-agent-dev
azd env select legal-agent-prod
```

### View Current Environment

```powershell
# Show current environment
azd env list

# Get all environment variables
azd env get-values
```

## Cost Management

### Estimated Monthly Costs

| Service | Tier | Estimated Cost |
|---------|------|----------------|
| Container Apps | 2 vCPU, 4GB RAM | ~$73/month |
| Azure AI Search | Standard | ~$250/month |
| Document Intelligence | S0 | Pay per use |
| Container Registry | Basic | ~$5/month |
| Key Vault | Standard | ~$3/month |
| Log Analytics | Pay-as-you-go | ~$10-50/month |
| **Total** | | **~$341-391/month** |

*Microsoft Foundry costs separate based on model and usage*

### Cost Optimization

```powershell
# Scale to zero during off-hours
az containerapp update --min-replicas 0 ...

# Use lower-tier services for dev
# Edit infra/main.bicep:
# - Search: basic tier
# - Container Apps: 1 vCPU, 2GB RAM
```

## Troubleshooting

### Issue: "azd: command not found"

**Solution**: Install Azure Developer CLI

```powershell
# Windows (PowerShell)
winget install microsoft.azd

# Or use installer
# https://aka.ms/install-azd.ps1
```

### Issue: "No subscription found"

**Solution**: Login to Azure

```powershell
az login
azd auth login
```

### Issue: "Deployment failed"

**Solution**: Check logs

```powershell
# View deployment logs
azd deploy --debug

# Check Azure Portal for specific errors
az portal
```

### Issue: "Container app not starting"

**Solution**: Check environment variables

```powershell
# Verify all required variables are set
azd env get-values

# Check container logs
az containerapp logs show --name ... --resource-group ... --follow
```

### Issue: "Search service quota exceeded"

**Solution**: Request quota increase

```powershell
# Check current quota
az search service show --name ... --resource-group ...

# Request increase in Azure Portal
# Or choose different region
```

## Clean Up Resources

### Delete Everything

```powershell
# Delete all resources (cannot be undone!)
azd down

# Or delete just the resource group
az group delete --name $(azd env get-value AZURE_RESOURCE_GROUP) --yes
```

### Keep Infrastructure, Undeploy App

```powershell
# Just remove the container app
az containerapp delete `
  --name $(azd env get-value AZURE_CONTAINER_APP_NAME) `
  --resource-group $(azd env get-value AZURE_RESOURCE_GROUP) `
  --yes
```

## CI/CD Integration

### GitHub Actions

azd automatically generates GitHub Actions workflows:

```powershell
# Initialize GitHub Actions
azd pipeline config

# Push to GitHub
git add .
git commit -m "Initial deployment setup"
git push
```

### Azure DevOps

```powershell
# Configure Azure DevOps pipeline
azd pipeline config --provider azdo
```

## Advanced Configuration

### Custom Domain

```powershell
# Add custom domain to Container App
az containerapp hostname add `
  --name $(azd env get-value AZURE_CONTAINER_APP_NAME) `
  --resource-group $(azd env get-value AZURE_RESOURCE_GROUP) `
  --hostname "legal-agent.yourdomain.com"
```

### Enable VNet Integration

Edit `infra/main.bicep` to add VNet support for private networking.

### Add Custom Secrets

```powershell
# Add secret to Key Vault
az keyvault secret set `
  --vault-name $(azd env get-value AZURE_KEYVAULT_NAME) `
  --name "custom-secret" `
  --value "secret-value"
```

## Next Steps

1. **Index Documents**: Upload legal documents to Azure AI Search
2. **Configure Model**: Fine-tune agent instructions in deployment
3. **Monitor**: Set up alerts in Application Insights
4. **Scale**: Adjust min/max replicas based on usage
5. **Secure**: Enable VNet integration for production
6. **Integrate**: Connect to your legal management systems

## Support Resources

- **azd Documentation**: [https://learn.microsoft.com/azure/developer/azure-developer-cli](https://learn.microsoft.com/azure/developer/azure-developer-cli)
- **Azure Container Apps**: [https://learn.microsoft.com/azure/container-apps](https://learn.microsoft.com/azure/container-apps)
- **Bicep Documentation**: [https://learn.microsoft.com/azure/azure-resource-manager/bicep](https://learn.microsoft.com/azure/azure-resource-manager/bicep)

## Quick Reference

```powershell
# Common commands
azd init              # Initialize new environment
azd provision         # Create Azure resources
azd deploy           # Deploy application
azd up               # Provision + deploy in one command
azd down             # Delete all resources
azd env list         # List environments
azd env get-values   # Show environment variables
azd show             # Display deployed resources
azd monitor          # Open Application Insights
```

---

**Ready to deploy?** Run: `azd up` (provisions + deploys in one command!)
