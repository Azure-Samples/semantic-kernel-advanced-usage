param uniqueId string
param prefix string
param userAssignedIdentityResourceId string
param userAssignedIdentityPrincipalId string
param messagesEndpoint string

resource bot 'Microsoft.BotService/botServices@2023-09-15-preview' = {
  name: '${prefix}bot${uniqueId}'
  location: 'global'
  properties: {
    displayName: '${prefix}bot${uniqueId}'
    endpoint: messagesEndpoint
    description: 'Bot created by Bicep'
    publicNetworkAccess: 'Enabled'
    msaAppId: userAssignedIdentityPrincipalId
    msaAppMSIResourceId: null
    schemaTransformationVersion: '1.3'    
  }
}
