// Azure Document Intelligence (Form Recognizer)
param name string
param location string = resourceGroup().location
param tags object = {}
param sku string = 'S0'

resource documentIntelligence 'Microsoft.CognitiveServices/accounts@2023-05-01' = {
  name: name
  location: location
  tags: tags
  kind: 'FormRecognizer'
  sku: {
    name: sku
  }
  properties: {
    customSubDomainName: name
    publicNetworkAccess: 'Enabled'
    networkAcls: {
      defaultAction: 'Allow'
    }
  }
}

output id string = documentIntelligence.id
output name string = documentIntelligence.name
output endpoint string = documentIntelligence.properties.endpoint
output key string = documentIntelligence.listKeys().key1
