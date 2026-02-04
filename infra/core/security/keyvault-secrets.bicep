// Store secrets in Key Vault
param keyVaultName string
@secure()
param searchApiKey string
@secure()
param documentIntelligenceKey string

resource keyVault 'Microsoft.KeyVault/vaults@2023-02-01' existing = {
  name: keyVaultName
}

resource searchApiKeySecret 'Microsoft.KeyVault/vaults/secrets@2023-02-01' = {
  parent: keyVault
  name: 'search-api-key'
  properties: {
    value: searchApiKey
  }
}

resource documentIntelligenceKeySecret 'Microsoft.KeyVault/vaults/secrets@2023-02-01' = {
  parent: keyVault
  name: 'document-intelligence-key'
  properties: {
    value: documentIntelligenceKey
  }
}

output searchApiKeySecretUri string = searchApiKeySecret.properties.secretUri
output documentIntelligenceKeySecretUri string = documentIntelligenceKeySecret.properties.secretUri
