param uniqueId string
param prefix string
param userAssignedIdentityResourceId string
param userAssignedIdentityClientId string
param openAiEndpoint string
param openAiApiKey string
param applicationInsightsConnectionString string
param containerRegistry string = '${prefix}acr${uniqueId}'
param location string = resourceGroup().location
param logAnalyticsWorkspaceName string
// param serviceBusNamespaceFqdn string
param cosmosDbEndpoint string
param cosmosDbDatabaseName string
param cosmosDbContainerName string
param agentAppExists bool
param chatAppExists bool
param emptyContainerImage string = 'mcr.microsoft.com/azuredocs/containerapps-helloworld:latest'

resource logAnalyticsWorkspace 'Microsoft.OperationalInsights/workspaces@2023-09-01' existing = {
  name: logAnalyticsWorkspaceName
}

// see https://azureossd.github.io/2023/01/03/Using-Managed-Identity-and-Bicep-to-pull-images-with-Azure-Container-Apps/
resource containerAppEnv 'Microsoft.App/managedEnvironments@2023-11-02-preview' = {
  name: '${prefix}-containerAppEnv-${uniqueId}'
  location: location
  identity: {
    type: 'UserAssigned'
    userAssignedIdentities: {
      '${userAssignedIdentityResourceId}': {}
    }
  }
  properties: {
    appLogsConfiguration: {
      destination: 'log-analytics'
      logAnalyticsConfiguration: {
        customerId: logAnalyticsWorkspace.properties.customerId
        sharedKey: logAnalyticsWorkspace.listKeys().primarySharedKey
      }
    }
  }
}

// resource daprPubSubAgents 'Microsoft.App/managedEnvironments/daprComponents@2024-10-02-preview' = {
//   name: 'workflow'
//   parent: containerAppEnv
//   properties: {
//     componentType: 'pubsub.azure.servicebus.topics'
//     version: 'v1'
//     scopes: [
//       'agents'
//     ]
//     metadata: [
//       {
//         // NOTE we don't wnat Dapr to manage the subscriptions
//         name: 'disableEntityManagement '
//         value: 'true'
//       }
//       {
//         name: 'consumerID'
//         value: 'workflow-input'
//       }
//       {
//         name: 'namespaceName'
//         value: serviceBusNamespaceFqdn
//       }
//       {
//         name: 'azureTenantId'
//         value: tenant().tenantId
//       }
//       {
//         name: 'azureClientId'
//         value: userAssignedIdentityClientId
//       }
//     ]
//   }
// }
// resource daprPubSubUI 'Microsoft.App/managedEnvironments/daprComponents@2024-10-02-preview' = {
//   name: 'ui'
//   parent: containerAppEnv
//   properties: {
//     componentType: 'pubsub.azure.servicebus.topics'
//     version: 'v1'
//     scopes: [
//       'ui'
//     ]
//     metadata: [
//       {
//         // NOTE we don't wnat Dapr to manage the subscriptions
//         name: 'disableEntityManagement '
//         value: 'true'
//       }
//       {
//         name: 'consumerID'
//         value: 'ui-updates'
//       }
//       {
//         name: 'namespaceName'
//         value: serviceBusNamespaceFqdn
//       }
//       {
//         name: 'azureTenantId'
//         value: tenant().tenantId
//       }
//       {
//         name: 'azureClientId'
//         value: userAssignedIdentityClientId
//       }
//     ]
//   }
// }

resource cosmosDaprComponent 'Microsoft.App/managedEnvironments/daprComponents@2024-10-02-preview' = {
  name: 'state'
  parent: containerAppEnv
  properties: {
    componentType: 'state.azure.cosmosdb'
    version: 'v1'
    scopes: [
      'agents'
    ]
    metadata: [
      {
        name: 'url'
        value: cosmosDbEndpoint
      }
      {
        name: 'database'
        value: cosmosDbDatabaseName
      }
      {
        name: 'collection'
        value: cosmosDbContainerName
      }
      {
        name: 'actorStateStore'
        value: 'true'
      }
      {
        name: 'azureTenantId'
        value: tenant().tenantId
      }
      {
        name: 'azureClientId'
        value: userAssignedIdentityClientId
      }
    ]
  }
}

// When azd passes parameters, it will tell if apps were already created
// In this case, we don't overwrite the existing image
// See https://johnnyreilly.com/using-azd-for-faster-incremental-azure-container-app-deployments-in-azure-devops#the-does-your-service-exist-parameter
module fetchLatestImageAgents './fetch-container-image.bicep' = {
  name: 'agents-app-image'
  params: {
    exists: agentAppExists
    name: '${prefix}-agents-${uniqueId}'
  }
}
module fetchLatestImageChat './fetch-container-image.bicep' = {
  name: 'chat-app-image'
  params: {
    exists: chatAppExists
    name: '${prefix}-chat-${uniqueId}'
  }
}

resource agentsContainerApp 'Microsoft.App/containerApps@2022-03-01' = {
  name: '${prefix}-agents-${uniqueId}'
  location: location
  tags: {'azd-service-name': 'agents' }
  identity: {
    type: 'UserAssigned'
    userAssignedIdentities: {
      '${userAssignedIdentityResourceId}': {}
    }
  }
  properties: {
    managedEnvironmentId: containerAppEnv.id
    configuration: {
      dapr: {
        enabled: true
        appId: 'agents'
        appPort: 80
      }
      activeRevisionsMode: 'Single'
      ingress: {
        external: true
        targetPort: 80
        transport: 'auto'
      }
      registries: [
        {
          server: '${containerRegistry}.azurecr.io'
          identity: userAssignedIdentityResourceId
        }
      ]
    }
    template: {
      scale: {
        minReplicas: 1
        maxReplicas: 1
      }
      containers: [
        {
          name: 'agents'
          image: agentAppExists ? fetchLatestImageAgents.outputs.containers[0].image : emptyContainerImage
          resources: {
            cpu: 2
            memory: '4Gi'
          }
          env: [
            // https://learn.microsoft.com/en-us/answers/questions/1225865/unable-to-get-a-user-assigned-managed-identity-wor
            { name: 'AZURE_CLIENT_ID', value: userAssignedIdentityClientId }
            { name: 'APPLICATIONINSIGHTS_CONNECTIONSTRING', value: applicationInsightsConnectionString }
            { name: 'APPLICATIONINSIGHTS_SERVICE_NAME', value: 'agents' }
            { name: 'AZURE_OPENAI_ENDPOINT', value: openAiEndpoint }
            { name: 'AZURE_OPENAI_MODEL', value: 'gpt-4o' }
            { name: 'AZURE_OPENAI_API_KEY', value: '' }
            { name: 'AZURE_OPENAI_API_VERSION', value: '2024-08-01-preview' }
            { name: 'SEMANTICKERNEL_EXPERIMENTAL_GENAI_ENABLE_OTEL_DIAGNOSTICS_SENSITIVE ', value: 'true' }
            // { name: 'PUBSUB_NAME', value: 'workflow' }
            // { name: 'TOPIC_NAME', value: 'events' }
          ]
        }
      ]
    }
  }
}

resource chatContainerApp 'Microsoft.App/containerApps@2023-11-02-preview' = {
  name: '${prefix}-chat-${uniqueId}'
  location: location
  tags: {'azd-service-name': 'chat' }
  identity: {
    type: 'UserAssigned'
    userAssignedIdentities: {
      '${userAssignedIdentityResourceId}': {}
    }
  }
  properties: {
    managedEnvironmentId: containerAppEnv.id
    configuration: {
      dapr: {
        enabled: true
        appId: 'chat'
        appPort: 80
      }
      activeRevisionsMode: 'Single'
      ingress: {
        external: true
        targetPort: 80
        transport: 'auto'
      }
      registries: [
        {
          server: '${containerRegistry}.azurecr.io'
          identity: userAssignedIdentityResourceId
        }
      ]
    }
    template: {
      scale: {
        minReplicas: 1
        maxReplicas: 1
      }
      containers: [
        {
          name: 'chat'
          image: chatAppExists ? fetchLatestImageChat.outputs.containers[0].image : emptyContainerImage
          resources: {
            cpu: 1
            memory: '2Gi'
          }
          env: [
            { name: 'AZURE_CLIENT_ID', value: userAssignedIdentityClientId }
            { name: 'APPLICATIONINSIGHTS_CONNECTIONSTRING', value: applicationInsightsConnectionString }
          ]
        }
      ]
    }
  }
}
