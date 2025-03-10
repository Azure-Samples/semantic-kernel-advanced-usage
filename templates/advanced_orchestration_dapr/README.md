# Semantic Kernel Advanced Customer Support

This repo showcases a sample AI-enabled customer support application that leverages [Semantic Kernel](https://github.com/microsoft/semantic-kernel) Agents boosted with:

- an improved [`SelectionStrategy`](src/agents/sk_ext/speaker_election_strategy.py) that accounts for agents descriptions and available tools to provide a more accurate selection (including the reason for it for traceability).
- _nested orchestration_ via [`Teams`](src/agents/sk_ext/team.py) and `Agents` for more complex, hierarchical routing scenarios.
- a special type of `Agent` named [`PlannedTeam`](src/agents/sk_ext/planned_team.py), which can handle more complex, cross-agent asks turning them into a multi-step process automatically.
- improved telemetry and explainability via [Application Insights](https://learn.microsoft.com/en-us/azure/azure-monitor/app/app-insights-overview) to track agentic team [steps](https://learn.microsoft.com/en-us/semantic-kernel/concepts/enterprise-readiness/observability/telemetry-with-console?tabs=Powershell-CreateFile%2CEnvironmentFile&pivots=programming-language-python#environment-variables) and [results](https://learn.microsoft.com/en-us/semantic-kernel/concepts/enterprise-readiness/observability/telemetry-with-app-insights?tabs=Powershell&pivots=programming-language-python#inspect-telemetry-data), as well as the reasoning behind agent selection.

Additionally, the application leverages [Azure Container Apps](https://learn.microsoft.com/en-us/azure/container-apps/) and [Dapr](https://dapr.io) to enable the [_Virtual Actor pattern_](https://docs.dapr.io/developing-applications/building-blocks/actors/actors-overview/) for agentic teams and natively handle `ChatHistory` persistence via Dapr's [state store](https://docs.dapr.io/developing-applications/building-blocks/state-management/), ensuring that the application can scale seamlessly.

## Rationale

- Default orchestration logic is based on the agent names only, which is not always sufficient to determine the best agent for a given ask.
- Complex asks may require the involvement of multiple agents in a row to _divide and conquer_ the task, which can be difficult to manage without a _goal-oriented_, _multi-step_ orchestration strategy.
- Hosting agents and orchestrator in the same process can lead to performance bottlenecks and maintainability issues.
- Persisting conversation state (`ChatHistory`) poses challenges in terms of scalability and reliability, especially to avoid concurrent writes to the same conversation.
- Tracking agentic team steps and results is important for debugging and improving the system.

## Visual Example

In this case, the user asks a question that requires the involvement of multiple agents, which are able to collaborate and produce a composite answer.

![Example chat demonstrating agents producing a composite answer](image.png)

## Telemetry and explanability example

### Waterfall chart of agentic team steps (Application Insights)

![Exaple waterfall chart of agentic team steps and results](telemetry.png)

### Additional debug information provided by the improved `SelectionStrategy`:

![alt text](telemetry_details.png)

### Azure AI Foundry tracing

See [official documentation](https://learn.microsoft.com/en-us/azure/ai-foundry/tracing) for more details.

![alt text](ai-foundry-tracing.png)

## Architecture

The overall architecture involves [Dapr](https://dapr.io) to enable the [_Virtual Actor pattern_](https://docs.dapr.io/developing-applications/building-blocks/actors/actors-overview/), in order to host the agentic team and natively handle `ChatHistory` persistence via Dapr's [state store](https://docs.dapr.io/developing-applications/building-blocks/state-management/).

```mermaid
flowchart TD
  %% User and client
  U[User]
  CB[Browser / Client]
  U --> CB

  %% Container Apps (Dapr enabled)
  subgraph "Azure Container Apps"
    Chat["`Chat App<br/>(Dapr enabled)<br/>[src/chat]`"]
    Agents["`Agents App<br/>(Dapr enabled)<br/>[src/agents]`"]
  end

  CB --> Chat

  %% Dapr sidecars within container apps
  Chat -- "Dapr Sidecar" --> DS1["`Dapr: state store<br/>(in-memory / Cosmos DB)`"]
  Agents -- "Dapr Sidecar" --> DS2[Dapr Components]

  %% Communication Flow
  Chat --- Agents
  Agents --- Chat

  %% Azure Services and Infrastructure
  subgraph "Azure Resources"
    ACR["`Azure Container Registry<br/>[infra/acr.bicep]`"]
    AI["`Application Insights<br/>[infra/appin.bicep]`"]
    LA["`Log Analytics<br/>[infra/appin.bicep]`"]
    OAI["`Azure OpenAI<br/>[infra/openAI.bicep]`"]
    Cosmos["`Cosmos DB<br/>[infra/cosmos.bicep]`"]
    UAMI["`User Assigned Identity<br/>[infra/uami.bicep]`"]
  end

  %% Deployment orchestration via Azure Developer CLI
  ADCLI["`Azure Developer CLI<br/>(azd)`"]
  ADCLI --> ACR
  ADCLI --> AI
  ADCLI --> LA
  ADCLI --> OAI
  ADCLI --> Cosmos
  ADCLI --> UAMI

  %% Container App image source
  ACR --> Chat
  ACR --> Agents

  %% Monitoring and Telemetry
  Chat --> AI
  Agents --> AI
  AI --> LA

  %% Data persistence via Dapr state store
  DS1 --> Cosmos

  %% Semantic Kernel
  SK["`Semantic Kernel<br/>(LLM Processing)`"]
  Agents --> SK
  SK --- Agents
```

## Getting Started

### Prerequisites

- **Python 3.12+**
- [**Azure Developer CLI**](https://learn.microsoft.com/en-us/azure/developer/azure-developer-cli/install-azd?tabs=winget-windows%2Cbrew-mac%2Cscript-linux&pivots=os-windows) – To deploy and manage Azure resources.
- **Docker** and [**Dapr CLI**](https://docs.dapr.io/getting-started/install-dapr-cli/) – To run the application locally.

### Clone the repo

```bash
git clone https://github.com/Azure-Samples/mas-sk-quickstart
cd mas-sk-quickstart
```

### Azure Deployment

> [!NOTE]
> Script will **NOT** create a new Azure OpenAI resource. You will need to have an existing one with a deployed model.

```bash
# Login to Azure if required
azd auth login --tenant-id <TENANT>.onmicrosoft.com

azd up

# When prompted, select
# - Azure subscription to deploy to
# - Azure region to deploy to
# - EXISTING Azure OpenAI resource and group to use (azd will NOT create a new one)
```

### Running Locally

> [!TIP]
> If you deployed the application to Azure, you can run it locally using the same Azure resources.
> Simply copy the `.env` file from the `.azure/<env name>` folder to the root of the repo.

1. `cp .env.example .env`
2. Update `.env` with your Azure OpenAI resource endpoint.
3. Ensure Docker is running.
4. Init Dapr (once only): `dapr init`.
5. Setup Python environment and install dependencies:

```bash
python -m venv .venv

# On macOS/Linux:
source .venv/bin/activate

# On Windows:
.venv\Scripts\Activate.ps1

pip install -r src/chat/requirements.txt
pip install -r src/agents/requirements.txt
```

To run:

`dapr run -f dapr.yaml`

## Contributing

This project welcomes contributions and suggestions. Please see [CONTRIBUTING.md](CONTRIBUTING.md) for details.

## License

This project is licensed under the MIT License. See [LICENSE.md](LICENSE.md) for details.
