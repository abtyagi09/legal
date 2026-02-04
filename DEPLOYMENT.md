# Deployment Guide - Legal Document Management AI Agent

This guide provides step-by-step instructions for deploying the Legal Document Management AI Agent to Azure Container Apps.

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Azure Service Setup](#azure-service-setup)
3. [Local Development Setup](#local-development-setup)
4. [Docker Deployment](#docker-deployment)
5. [Azure Container Apps Deployment](#azure-container-apps-deployment)
6. [Configuration Management](#configuration-management)
7. [Monitoring and Logging](#monitoring-and-logging)
8. [Troubleshooting](#troubleshooting)

## Prerequisites

Before deploying, ensure you have:

- **Azure Subscription** with appropriate permissions
- **Azure CLI** installed ([Install Guide](https://learn.microsoft.com/en-us/cli/azure/install-azure-cli))
- **Docker** installed for containerization
- **Python 3.10+** for local development
- **Microsoft Foundry** (formerly Azure AI Foundry) project access

## Azure Service Setup

### 1. Create Microsoft Foundry Project

1. Navigate to [Microsoft Foundry](https://ai.azure.com/) (formerly Azure AI Foundry)
2. Create a new project or use an existing one
3. Deploy a model (recommended: **GPT-5** or **Claude Sonnet 4.5**)
4. Note down:
   - Project endpoint (e.g., `https://your-project.api.azureml.ms`)
   - Model deployment name

> **Tip**: Use AI Toolkit in VS Code to browse and deploy Foundry models easily.

### 2. Create Azure AI Search Service

```bash
# Login to Azure
az login

# Set variables
RESOURCE_GROUP="legal-agent-rg"
LOCATION="eastus"
SEARCH_SERVICE_NAME="legal-search-service"

# Create resource group
az group create --name $RESOURCE_GROUP --location $LOCATION

# Create Azure AI Search service
az search service create \
  --name $SEARCH_SERVICE_NAME \
  --resource-group $RESOURCE_GROUP \
  --sku standard \
  --location $LOCATION

# Get API key
az search admin-key show \
  --resource-group $RESOURCE_GROUP \
  --service-name $SEARCH_SERVICE_NAME
```

### 3. Create Azure Document Intelligence Service

```bash
DOC_INTEL_NAME="legal-doc-intel"

# Create Document Intelligence service
az cognitiveservices account create \
  --name $DOC_INTEL_NAME \
  --resource-group $RESOURCE_GROUP \
  --kind FormRecognizer \
  --sku S0 \
  --location $LOCATION

# Get endpoint and key
az cognitiveservices account show \
  --name $DOC_INTEL_NAME \
  --resource-group $RESOURCE_GROUP \
  --query properties.endpoint

az cognitiveservices account keys list \
  --name $DOC_INTEL_NAME \
  --resource-group $RESOURCE_GROUP
```

### 4. Create Azure AI Search Index

Create an index for your legal documents with the following schema:

```json
{
  "name": "legal-documents-index",
  "fields": [
    {"name": "id", "type": "Edm.String", "key": true},
    {"name": "title", "type": "Edm.String", "searchable": true},
    {"name": "content", "type": "Edm.String", "searchable": true},
    {"name": "document_type", "type": "Edm.String", "filterable": true},
    {"name": "document_date", "type": "Edm.DateTimeOffset", "filterable": true, "sortable": true},
    {"name": "author", "type": "Edm.String", "filterable": true},
    {"name": "parties", "type": "Edm.String", "searchable": true}
  ],
  "semanticConfiguration": {
    "defaultConfiguration": "default",
    "configurations": [
      {
        "name": "default",
        "prioritizedFields": {
          "titleField": {"fieldName": "title"},
          "contentFields": [{"fieldName": "content"}],
          "keywordsFields": [{"fieldName": "document_type"}]
        }
      }
    ]
  }
}
```

You can create the index using the Azure Portal or Azure AI Search REST API.

## Local Development Setup

### 1. Clone and Install Dependencies

```bash
# Navigate to project directory
cd c:\agents\legal

# Create virtual environment
python -m venv venv

# Activate virtual environment
# Windows:
venv\Scripts\activate
# Linux/Mac:
source venv/bin/activate

# Install dependencies (--pre flag is REQUIRED for Agent Framework)
pip install -r requirements.txt --pre
```

### 2. Configure Application

```bash
# Copy example configuration
cp config.example.yaml config.yaml

# Edit config.yaml with your Azure service credentials
notepad config.yaml  # or use your preferred editor
```

Update the following in `config.yaml`:
- `foundry.project_endpoint`
- `foundry.model_deployment_name`
- `search.service_endpoint`
- `search.api_key`
- `search.index_name`
- `document_intelligence.endpoint`
- `document_intelligence.api_key`

### 3. Run Locally

```bash
# Run the agent
python src/main.py
```

## Docker Deployment

### 1. Build Docker Image

```bash
# Build the image
docker build -t legal-document-agent:latest .

# Verify the build
docker images | grep legal-document-agent
```

### 2. Run with Docker Compose

```bash
# Update config.yaml with your credentials
# Then run with Docker Compose
docker-compose up -d

# View logs
docker-compose logs -f legal-agent

# Stop the container
docker-compose down
```

## Azure Container Apps Deployment

### 1. Create Container Registry

```bash
ACR_NAME="legalagentacr"

# Create Azure Container Registry
az acr create \
  --name $ACR_NAME \
  --resource-group $RESOURCE_GROUP \
  --sku Basic \
  --admin-enabled true

# Login to ACR
az acr login --name $ACR_NAME
```

### 2. Push Image to ACR

```bash
# Tag image for ACR
docker tag legal-document-agent:latest $ACR_NAME.azurecr.io/legal-document-agent:latest

# Push to ACR
docker push $ACR_NAME.azurecr.io/legal-document-agent:latest
```

### 3. Create Container Apps Environment

```bash
CONTAINERAPPS_ENV="legal-agent-env"

# Create Container Apps environment
az containerapp env create \
  --name $CONTAINERAPPS_ENV \
  --resource-group $RESOURCE_GROUP \
  --location $LOCATION
```

### 4. Deploy to Container Apps

```bash
APP_NAME="legal-document-agent"

# Get ACR credentials
ACR_USERNAME=$(az acr credential show --name $ACR_NAME --query username -o tsv)
ACR_PASSWORD=$(az acr credential show --name $ACR_NAME --query passwords[0].value -o tsv)

# Create Container App
az containerapp create \
  --name $APP_NAME \
  --resource-group $RESOURCE_GROUP \
  --environment $CONTAINERAPPS_ENV \
  --image $ACR_NAME.azurecr.io/legal-document-agent:latest \
  --registry-server $ACR_NAME.azurecr.io \
  --registry-username $ACR_USERNAME \
  --registry-password $ACR_PASSWORD \
  --cpu 2.0 \
  --memory 4.0Gi \
  --min-replicas 1 \
  --max-replicas 5 \
  --target-port 8000 \
  --ingress external \
  --secrets \
    foundry-endpoint=<your-foundry-endpoint> \
    search-api-key=<your-search-api-key> \
    doc-intel-api-key=<your-doc-intel-api-key> \
  --env-vars \
    AZURE_CLIENT_ID=secretref:azure-client-id \
    AZURE_TENANT_ID=secretref:azure-tenant-id
```

### 5. Configure Managed Identity (Recommended)

For production, use managed identity instead of API keys:

```bash
# Enable system-assigned managed identity
az containerapp identity assign \
  --name $APP_NAME \
  --resource-group $RESOURCE_GROUP \
  --system-assigned

# Get the identity principal ID
IDENTITY_ID=$(az containerapp identity show \
  --name $APP_NAME \
  --resource-group $RESOURCE_GROUP \
  --query principalId -o tsv)

# Grant permissions to Azure services
# For Azure AI Search
az role assignment create \
  --role "Search Index Data Reader" \
  --assignee $IDENTITY_ID \
  --scope /subscriptions/<subscription-id>/resourceGroups/$RESOURCE_GROUP/providers/Microsoft.Search/searchServices/$SEARCH_SERVICE_NAME
```

## Configuration Management

### Using Azure Key Vault (Recommended for Production)

```bash
KEYVAULT_NAME="legal-agent-kv"

# Create Key Vault
az keyvault create \
  --name $KEYVAULT_NAME \
  --resource-group $RESOURCE_GROUP \
  --location $LOCATION

# Store secrets
az keyvault secret set \
  --vault-name $KEYVAULT_NAME \
  --name "search-api-key" \
  --value "<your-search-api-key>"

az keyvault secret set \
  --vault-name $KEYVAULT_NAME \
  --name "doc-intel-api-key" \
  --value "<your-doc-intel-api-key>"

# Grant Container App access to Key Vault
az keyvault set-policy \
  --name $KEYVAULT_NAME \
  --object-id $IDENTITY_ID \
  --secret-permissions get list
```

## Monitoring and Logging

### 1. Enable Application Insights

```bash
APPINSIGHTS_NAME="legal-agent-insights"

# Create Application Insights
az monitor app-insights component create \
  --app $APPINSIGHTS_NAME \
  --location $LOCATION \
  --resource-group $RESOURCE_GROUP

# Get instrumentation key
az monitor app-insights component show \
  --app $APPINSIGHTS_NAME \
  --resource-group $RESOURCE_GROUP \
  --query instrumentationKey -o tsv
```

### 2. View Logs

```bash
# Stream logs from Container App
az containerapp logs show \
  --name $APP_NAME \
  --resource-group $RESOURCE_GROUP \
  --follow

# Query logs
az monitor app-insights query \
  --app $APPINSIGHTS_NAME \
  --analytics-query "traces | where timestamp > ago(1h) | order by timestamp desc"
```

## Troubleshooting

### Common Issues

#### 1. "Configuration file not found"
**Solution**: Ensure `config.yaml` exists and is properly mounted in the container.

```bash
# For Docker Compose, verify the volume mount
docker-compose config | grep config.yaml
```

#### 2. "Authentication failed"
**Solution**: Verify Azure credentials and managed identity permissions.

```bash
# Test Azure CLI authentication
az account show

# Verify managed identity is enabled
az containerapp identity show --name $APP_NAME --resource-group $RESOURCE_GROUP
```

#### 3. "Agent Framework module not found"
**Solution**: Ensure `--pre` flag was used during pip install.

```bash
pip install agent-framework-azure-ai --pre
```

#### 4. "Search index not found"
**Solution**: Verify the index exists and the name matches your configuration.

```bash
az search index list \
  --service-name $SEARCH_SERVICE_NAME \
  --resource-group $RESOURCE_GROUP
```

### Debug Mode

Enable debug logging by updating `config.yaml`:

```yaml
logging:
  level: "DEBUG"
```

Or set environment variable:

```bash
export LOG_LEVEL=DEBUG
python src/main.py
```

## Production Best Practices

1. **Use Managed Identity**: Avoid storing API keys in configuration files
2. **Enable HTTPS**: Always use HTTPS for external ingress
3. **Implement Rate Limiting**: Protect against abuse
4. **Monitor Costs**: Set up budget alerts for Azure services
5. **Regular Updates**: Keep dependencies updated, especially Agent Framework
6. **Backup Configuration**: Store configuration in Azure Key Vault
7. **Health Checks**: Configure liveness and readiness probes
8. **Scaling**: Configure autoscaling based on load
9. **Security**: Implement network isolation using VNet integration
10. **Testing**: Test with sample legal documents before production use

## Support and Resources

- **Microsoft Agent Framework**: [GitHub Repository](https://github.com/microsoft/agent-framework)
- **Azure AI Search**: [Documentation](https://learn.microsoft.com/en-us/azure/search/)
- **Azure Document Intelligence**: [Documentation](https://learn.microsoft.com/en-us/azure/ai-services/document-intelligence/)
- **Azure Container Apps**: [Documentation](https://learn.microsoft.com/en-us/azure/container-apps/)
- **Microsoft Foundry**: [Portal](https://ai.azure.com/)

## Next Steps

After deployment:

1. **Index Documents**: Upload and index your legal documents to Azure AI Search
2. **Test Search**: Verify search functionality with sample queries
3. **Customize Agent**: Adjust agent instructions for your specific legal workflows
4. **Scale**: Configure autoscaling rules based on your usage patterns
5. **Integrate**: Connect the agent to your existing legal management systems

---

For issues or questions, please refer to the main [README.md](README.md) or open an issue in the project repository.
