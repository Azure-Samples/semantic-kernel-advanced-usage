targetScope = 'subscription'

@minLength(1)
@maxLength(64)
@description('Name of the environment that can be used as part of naming resource convention')
param environmentName string

@description('The current user ID, to assign RBAC permissions to')
param currentUserId string

// Main deployment parameters
param prefix string = 'dev'
@minLength(1)
@description('Primary location for all resources')
param location string

@minLength(1)
@description('Name of the Azure OpenAI resource')
param openAIName string

@minLength(1)
@description('Name of the Azure Resource Group where the OpenAI resource is located')
param openAIResourceGroupName string

param openAIModel string
param openAIApiVersion string
param agentAppExists bool = false
param chatAppExists bool = false
param runningOnGh string = ''

var tags = {
  'azd-env-name': environmentName
}

resource rg 'Microsoft.Resources/resourceGroups@2022-09-01' = {
  name: 'rg-${environmentName}'
  location: location
  tags: tags
}

var uniqueId = uniqueString(rg.id)
var principalType = empty(runningOnGh) ? 'User' : 'ServicePrincipal'

module uami './uami.bicep' = {
  name: 'uami'
  scope: rg
  params: {
    uniqueId: uniqueId
    prefix: prefix
    location: location
  }
}

module appin './appin.bicep' = {
  name: 'appin'
  scope: rg
  params: {
    uniqueId: uniqueId
    prefix: prefix
    location: location
    userAssignedIdentityPrincipalId: uami.outputs.principalId
  }
}

module acrModule './acr.bicep' = {
  name: 'acr'
  scope: rg
  params: {
    uniqueId: uniqueId
    prefix: prefix
    userAssignedIdentityPrincipalId: uami.outputs.principalId
    location: location
  }
}

module openAI './openAI.bicep' = {
  name: 'openAI'
  scope: resourceGroup(openAIResourceGroupName)
  params: {
    openAIName: openAIName
    userAssignedIdentityPrincipalId: uami.outputs.principalId
  }
}

module cosmos 'cosmos.bicep' = {
  name: 'cosmos'
  scope: rg
  params: {
    uniqueId: uniqueId
    prefix: prefix
    userAssignedIdentityPrincipalId: uami.outputs.principalId
    currentUserId: principalType == 'User' ? currentUserId : ''
  }
}

// module sb 'br/public:avm/res/service-bus/namespace:0.11.2' = {
//   name: 'sb'
//   scope: rg
//   params: {
//     name: '${prefix}-sb-${uniqueId}'
//     topics: [
//       {
//         name: 'events'
//         requiresDuplicateDetection: false
//         subscriptions: [
//           {
//             name: 'dump' // For debugging purposes
//           }
//           {
//             name: 'approvals'
//             rules: [
//               {
//                 name: 'approvals'
//                 sqlFilter: {
//                   sqlExpression: 'source = \'approver_user\' and type = \'stop\''
//                 }
//               }
//             ]
//           }
//           {
//             name: 'workflow-input'
//             rules: [
//               {
//                 name: 'workflow-input'
//                 sqlFilter: {
//                   sqlExpression: 'type = \'input\''
//                 }
//               }
//             ]
//           }
//           {
//             name: 'ui-updates'
//             rules: [
//               {
//                 name: 'ui-updates'
//                 sqlFilter: {
//                   sqlExpression: 'type = \'update\''
//                 }
//               }
//             ]
//           }
//         ]
//       }
//     ]
//     roleAssignments: concat(
//       [
//         {
//           principalId: uami.outputs.principalId
//           principalType: 'ServicePrincipal'
//           roleDefinitionIdOrName: 'Azure Service Bus Data Owner'
//         }
//       ],
//       principalType == 'User' ? [
//         {
//           principalId: currentUserId
//           principalType: 'User'
//           roleDefinitionIdOrName: 'Azure Service Bus Data Owner'
//         }
//       ] : []
//     )
//   }
// }


// module logicapp './logicapp.bicep' = {
//   name: 'logic-app'
//   scope: rg
//   params: {
//     uniqueId: uniqueId
//     prefix: prefix
//     location: location
//     userAssignedIdentityResourceId: uami.outputs.identityId
//     logAnalyticsWorkspaceId: appin.outputs.logAnalyticsWorkspaceId
//     serviceBusName: sb.outputs.name
//   }
// }


module aca './aca.bicep' = {
  name: 'aca'
  scope: rg
  params: {
    uniqueId: uniqueId
    prefix: prefix
    userAssignedIdentityResourceId: uami.outputs.identityId
    containerRegistry: acrModule.outputs.acrName
    location: location
    logAnalyticsWorkspaceName: appin.outputs.logAnalyticsWorkspaceName
    applicationInsightsConnectionString: appin.outputs.applicationInsightsConnectionString
    openAiApiKey: '' // Force ManId, otherwise set openAI.listKeys().key1
    openAiEndpoint: openAI.outputs.openAIEndpoint
    // serviceBusNamespaceFqdn: '${sb.outputs.name}.servicebus.windows.net'
    cosmosDbEndpoint: cosmos.outputs.cosmosDbEndpoint
    cosmosDbDatabaseName: cosmos.outputs.cosmosDbDatabase
    cosmosDbContainerName: cosmos.outputs.cosmosDbContainer
    userAssignedIdentityClientId: uami.outputs.clientId
    agentAppExists: agentAppExists
    chatAppExists: chatAppExists
  }
}

// These outputs are copied by azd to .azure/<env name>/.env file
// post provision script will use these values, too
output AZURE_RESOURCE_GROUP string = rg.name
output APPLICATIONINSIGHTS_CONNECTIONSTRING string = appin.outputs.applicationInsightsConnectionString
output AZURE_TENANT_ID string = subscription().tenantId
output AZURE_USER_ASSIGNED_IDENTITY_ID string = uami.outputs.identityId
output AZURE_CONTAINER_REGISTRY_ENDPOINT string = acrModule.outputs.acrEndpoint
output AZURE_OPENAI_MODEL string = openAIModel
output AZURE_OPENAI_ENDPOINT string = openAI.outputs.openAIEndpoint
output AZURE_OPENAI_API_VERSION string = openAIApiVersion
