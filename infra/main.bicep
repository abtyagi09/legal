// Main Bicep file for Legal Document Agent infrastructure
targetScope = 'subscription'

@minLength(1)
@maxLength(64)
@description('Name of the environment used to generate a short unique hash for resources.')
param environmentName string

@minLength(1)
@description('Primary location for all resources')
param location string

@description('Id of the principal to assign database and application roles')
param principalId string = ''

@description('Name of the resource group')
param resourceGroupName string = ''

@description('Name of the container apps environment')
param containerAppsEnvironmentName string = ''

@description('Name of the container registry')
param containerRegistryName string = ''

@description('Name of the container app')
param containerAppName string = ''

@description('Name of the AI Search service')
param searchServiceName string = ''

@description('Name of the Document Intelligence service')
param documentIntelligenceName string = ''

@description('Name of the Log Analytics workspace')
param logAnalyticsWorkspaceName string = ''

@description('Name of the Application Insights instance')
param applicationInsightsName string = ''

@description('Name of the Key Vault')
param keyVaultName string = ''

@description('Microsoft Foundry project endpoint')
param foundryEndpoint string = ''

@description('Microsoft Foundry model deployment name')
param foundryModelDeployment string = ''

// Tags to apply to all resources
var tags = {
  'azd-env-name': environmentName
  'application': 'legal-document-agent'
  'managed-by': 'azure-developer-cli'
}

// Generate unique names if not provided
var abbrs = loadJsonContent('./abbreviations.json')
var resourceToken = toLower(uniqueString(subscription().id, environmentName, location))

// Resource group
resource rg 'Microsoft.Resources/resourceGroups@2021-04-01' = {
  name: !empty(resourceGroupName) ? resourceGroupName : '${abbrs.resourcesResourceGroups}${environmentName}'
  location: location
  tags: tags
}

// Log Analytics workspace
module logAnalytics './core/monitor/loganalytics.bicep' = {
  name: 'loganalytics'
  scope: rg
  params: {
    name: !empty(logAnalyticsWorkspaceName) ? logAnalyticsWorkspaceName : '${abbrs.operationalInsightsWorkspaces}${resourceToken}'
    location: location
    tags: tags
  }
}

// Application Insights
module applicationInsights './core/monitor/applicationinsights.bicep' = {
  name: 'applicationinsights'
  scope: rg
  params: {
    name: !empty(applicationInsightsName) ? applicationInsightsName : '${abbrs.insightsComponents}${resourceToken}'
    location: location
    tags: tags
    logAnalyticsWorkspaceId: logAnalytics.outputs.id
  }
}

// Container Registry
module containerRegistry './core/host/container-registry.bicep' = {
  name: 'containerregistry'
  scope: rg
  params: {
    name: !empty(containerRegistryName) ? containerRegistryName : '${abbrs.containerRegistryRegistries}${resourceToken}'
    location: location
    tags: tags
  }
}

// Azure AI Search
module searchService './core/ai/search.bicep' = {
  name: 'search'
  scope: rg
  params: {
    name: !empty(searchServiceName) ? searchServiceName : '${abbrs.searchSearchServices}${resourceToken}'
    location: location
    tags: tags
    sku: 'standard'
    replicaCount: 1
    partitionCount: 1
  }
}

// Azure Document Intelligence
module documentIntelligence './core/ai/documentintelligence.bicep' = {
  name: 'documentintelligence'
  scope: rg
  params: {
    name: !empty(documentIntelligenceName) ? documentIntelligenceName : '${abbrs.cognitiveServicesAccounts}${resourceToken}'
    location: location
    tags: tags
    sku: 'S0'
  }
}

// Key Vault
module keyVault './core/security/keyvault.bicep' = {
  name: 'keyvault'
  scope: rg
  params: {
    name: !empty(keyVaultName) ? keyVaultName : '${abbrs.keyVaultVaults}${resourceToken}'
    location: location
    tags: tags
    principalId: principalId
  }
}

// Store secrets in Key Vault
module secrets './core/security/keyvault-secrets.bicep' = {
  name: 'keyvault-secrets'
  scope: rg
  params: {
    keyVaultName: keyVault.outputs.name
    searchApiKey: searchService.outputs.apiKey
    documentIntelligenceKey: documentIntelligence.outputs.key
  }
}

// Container Apps Environment
module containerAppsEnvironment './core/host/container-apps-environment.bicep' = {
  name: 'containerappsenvironment'
  scope: rg
  params: {
    name: !empty(containerAppsEnvironmentName) ? containerAppsEnvironmentName : '${abbrs.appManagedEnvironments}${resourceToken}'
    location: location
    tags: tags
    logAnalyticsWorkspaceName: logAnalytics.outputs.name
  }
}

// Container App
module containerApp './core/host/container-app.bicep' = {
  name: 'containerapp'
  scope: rg
  params: {
    name: !empty(containerAppName) ? containerAppName : '${abbrs.appContainerApps}${resourceToken}'
    location: location
    tags: tags
    containerAppsEnvironmentId: containerAppsEnvironment.outputs.id
    containerRegistryName: containerRegistry.outputs.name
    imageName: 'legal-document-agent:latest'
    environmentVariables: [
      {
        name: 'FOUNDRY_ENDPOINT'
        value: foundryEndpoint
      }
      {
        name: 'FOUNDRY_MODEL_DEPLOYMENT'
        value: foundryModelDeployment
      }
      {
        name: 'SEARCH_ENDPOINT'
        value: searchService.outputs.endpoint
      }
      {
        name: 'SEARCH_INDEX_NAME'
        value: 'legal-documents-index'
      }
      {
        name: 'DOCUMENT_INTELLIGENCE_ENDPOINT'
        value: documentIntelligence.outputs.endpoint
      }
      {
        name: 'KEYVAULT_ENDPOINT'
        value: keyVault.outputs.endpoint
      }
      {
        name: 'APPLICATIONINSIGHTS_CONNECTION_STRING'
        value: applicationInsights.outputs.connectionString
      }
    ]
    cpu: '2.0'
    memory: '4Gi'
    minReplicas: 1
    maxReplicas: 5
  }
}

// Assign roles to Container App managed identity
module searchRoleAssignment './core/security/role-assignment.bicep' = {
  name: 'search-role-assignment'
  scope: rg
  params: {
    principalId: containerApp.outputs.identityPrincipalId
    roleDefinitionId: '1407120a-92aa-4202-b7e9-c0e197c71c8f' // Search Index Data Reader
    principalType: 'ServicePrincipal'
  }
}

module documentIntelligenceRoleAssignment './core/security/role-assignment.bicep' = {
  name: 'docintel-role-assignment'
  scope: rg
  params: {
    principalId: containerApp.outputs.identityPrincipalId
    roleDefinitionId: 'a97b65f3-24c7-4388-baec-2e87135dc908' // Cognitive Services User
    principalType: 'ServicePrincipal'
  }
}

module keyVaultRoleAssignment './core/security/role-assignment.bicep' = {
  name: 'keyvault-role-assignment'
  scope: rg
  params: {
    principalId: containerApp.outputs.identityPrincipalId
    roleDefinitionId: '4633458b-17de-408a-b874-0445c86b69e6' // Key Vault Secrets User
    principalType: 'ServicePrincipal'
  }
}

// Outputs
output AZURE_LOCATION string = location
output AZURE_RESOURCE_GROUP string = rg.name
output AZURE_CONTAINER_REGISTRY_ENDPOINT string = containerRegistry.outputs.loginServer
output AZURE_CONTAINER_REGISTRY_NAME string = containerRegistry.outputs.name
output AZURE_CONTAINER_APP_NAME string = containerApp.outputs.name
output AZURE_CONTAINER_APP_URL string = containerApp.outputs.uri
output AZURE_SEARCH_ENDPOINT string = searchService.outputs.endpoint
output AZURE_SEARCH_NAME string = searchService.outputs.name
output AZURE_DOCUMENT_INTELLIGENCE_ENDPOINT string = documentIntelligence.outputs.endpoint
output AZURE_DOCUMENT_INTELLIGENCE_NAME string = documentIntelligence.outputs.name
output AZURE_KEYVAULT_ENDPOINT string = keyVault.outputs.endpoint
output AZURE_KEYVAULT_NAME string = keyVault.outputs.name
output APPLICATIONINSIGHTS_CONNECTION_STRING string = applicationInsights.outputs.connectionString
