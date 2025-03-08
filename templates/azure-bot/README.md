# Extend Copilot Studio with Semantic Kernel

This template demonstrates how to build a [Copilot Studio Skill](https://learn.microsoft.com/en-us/microsoft-copilot-studio/configuration-add-skills#troubleshoot-errors-during-skill-registration) that allows to extend agent capabilities with a custom API running in Azure with the help of the Semantic Kernel.

## Rationale

[Microsoft Copilot Studio](https://learn.microsoft.com/en-us/microsoft-copilot-studio/fundamentals-what-is-copilot-studio) is a graphical, low-code tool for both creating an agent — including building automation with Power Automate — and extending a Microsoft 365 Copilot with your own enterprise data and scenarios.

However, in some cases you may need to extend the default agent capabilities by leveraing a pro-code approach, where specific requirements apply.

## Prerequisites

- Azure Subscription
- Azure CLI
- Azure Developer CLI
- Python 3.12 or later
- A Microsoft 365 tenant with Copilot Studio enabled

> [!NOTE]
> You don't need the Azure subscription to be on the same tenant as the Microsoft 365 tenant where Copilot Studio is enabled.
>
> However, you need to have the necessary permissions to register an application in the Azure Active Directory of the tenant where Copilot Studio is enabled.

## Getting Started

1. Clone this repository to your local machine.

```bash
git clone https://github.com/Azure-Samples/semantic-kernel-advanced-usage
cd semantic-kernel-advanced-usage/templates/azure-bot
```

2. Create a App Registration in Azure Entra ID, with a client secret.

```powershell
az login --tenant <COPILOT-tenant-id>
$appId = az ad app create --display-name "MyCopilotSkill" --query appId -o tsv
$secret = az ad app credential reset --id $appId --append --query password -o tsv
```

4. Run `azd up` to deploy the Azure resources.

```bash
azd auth login --tenant <AZURE-tenant-id>
azd up
```

> [!NOTE]
> When prompted, provide the `botAppId`, `botPassword` and `botTenantId` values from above.
>
> You will also need to input and existing Azure OpenAI resource name and its resource group.

## Implementation
