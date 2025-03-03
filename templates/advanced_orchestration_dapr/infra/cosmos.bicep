param uniqueId string
param prefix string
param userAssignedIdentityPrincipalId string
param cosmosDbAccountName string = '${prefix}cosmos${uniqueId}'
param databaseName string = 'agents-escalation'
param containerName string = 'conversations'
param location string = resourceGroup().location
param currentUserId string

// Create Cosmos DB account
resource cosmosDbAccount 'Microsoft.DocumentDB/databaseAccounts@2024-05-15' = {
  name: cosmosDbAccountName
  location: location
  kind: 'GlobalDocumentDB'
  properties: {
    databaseAccountOfferType: 'Standard'
    locations: [
      {
        locationName: location
        failoverPriority: 0
        isZoneRedundant: false
      }
    ]
    consistencyPolicy: {
      defaultConsistencyLevel: 'Session'
    }
  }
}

// Assign the User Assigned Identity Contributor role to the Cosmos DB account
resource cosmosDbAccountRoleAssignment 'Microsoft.Authorization/roleAssignments@2020-04-01-preview' = {
  name: guid(cosmosDbAccount.id, userAssignedIdentityPrincipalId, 'cosmosDbContributor')
  scope: cosmosDbAccount
  properties: {
    roleDefinitionId: resourceId('Microsoft.Authorization/roleDefinitions', 'b24988ac-6180-42a0-ab88-20f7382dd24c') // Role definition ID for Contributor
    principalId: userAssignedIdentityPrincipalId
    principalType: 'ServicePrincipal'
  }
}

// Create a database within the Cosmos DB account
resource cosmosDbDatabase 'Microsoft.DocumentDB/databaseAccounts/sqlDatabases@2024-05-15' = {
  name: databaseName
  parent: cosmosDbAccount
  properties: {
    resource: {
      id: databaseName
    }
    options: {}
  }
}

resource container 'Microsoft.DocumentDB/databaseAccounts/sqlDatabases/containers@2024-05-15' = {
  name: containerName
  location: location
  parent: cosmosDbDatabase
  properties: {
    resource: {
      id: containerName
      createMode: 'Default'
      partitionKey: {
        kind: 'Hash'
        paths: [
          '/partitionKey'
        ]
      }
    }
    options: {
    }
  }
}

/*
  SEE
    https://github.com/Azure/azure-quickstart-templates/blob/master/quickstarts/microsoft.kusto/kusto-cosmos-db/main.bicep
    https://learn.microsoft.com/en-us/azure/cosmos-db/how-to-setup-rbac#permission-model
*/
var cosmosDataContributor = '00000000-0000-0000-0000-000000000002'
resource sqlRoleAssignment 'Microsoft.DocumentDB/databaseAccounts/sqlRoleAssignments@2021-04-15' = {
  name: guid(cosmosDataContributor, userAssignedIdentityPrincipalId, cosmosDbAccount.id)
  parent: cosmosDbAccount
  properties: {
    roleDefinitionId: resourceId('Microsoft.DocumentDB/databaseAccounts/sqlRoleDefinitions', cosmosDbAccountName, cosmosDataContributor)
    principalId: userAssignedIdentityPrincipalId
    scope: cosmosDbAccount.id
  }
}
// Assign the User Assigned Identity Contributor role to the Cosmos DB account for the current user
resource sqlRoleAssignmentUser 'Microsoft.DocumentDB/databaseAccounts/sqlRoleAssignments@2021-04-15' = if(currentUserId != '') {
  name: guid(cosmosDataContributor, currentUserId, cosmosDbAccount.id)
  parent: cosmosDbAccount
  properties: {
    roleDefinitionId: resourceId('Microsoft.DocumentDB/databaseAccounts/sqlRoleDefinitions', cosmosDbAccountName, cosmosDataContributor)
    principalId: currentUserId
    scope: cosmosDbAccount.id
  }
}

output cosmosDbDatabase string = cosmosDbDatabase.name
output cosmosDbContainer string = container.name
output cosmosDbEndpoint string = cosmosDbAccount.properties.documentEndpoint
