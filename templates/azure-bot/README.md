# Azure Bot

This template demonstrates how to build an Azure Bot integrated with Microsoft Teams and powered by [Semantic Kernel](https://github.com/microsoft/semantic-kernel). The bot leverages advanced LLM capabilities and is designed to run as a cloud-native service on [Azure Container Apps](https://docs.microsoft.com/en-us/azure/container-apps/).

## Rationale

## Folder Structure

- **src/api:** Contains the API implementation (FastAPI app, bot logic, and configuration).
- **infra:** Bicep templates to deploy Azure resources (Container Apps, Azure OpenAI, Cosmos DB, etc.).
- **appPackage:** Resources required for the Microsoft Teams bot manifest and assets.

## Prerequisites

- Python 3.12+
- An [Azure account](https://azure.microsoft.com/en-us/free/) with the required permissions
- [Azure Developer CLI](https://learn.microsoft.com/en-us/azure/developer/azure-developer-cli/)
- Docker (for local testing)

## Setup and Running Locally

1. **Clone the Repository:**

   ```bash
   git clone https://github.com/Azure-Samples/semantic-kernel-advanced-usage.git
   cd templates/azure-bot
   ```

2. **Configure Environment Variables:**

   - Rename the `.env.sample` (if provided) to `.env` and update the values:
     ```bash
     cp .env.sample .env
     ```
   - Alternatively, set the required environment variables in your deployment environment.

3. **Create a Virtual Environment and Install Dependencies:**

   ```bash
   python -m venv .venv
   # On Windows:
   .venv\Scripts\Activate.ps1
   # On macOS/Linux:
   source .venv/bin/activate
   pip install -r src/api/requirements.txt
   ```

4. **Run the Application Locally:**

   ```bash
   uvicorn app:app --host 0.0.0.0 --port 80
   ```

## Deployment

The `infra` folder contains Bicep templates for deploying the required Azure resources. To deploy using the Azure Developer CLI, run:

```bash
azd up
```

You'll be prompted to select the Azure subscription, region, and existing resources (including an Azure OpenAI resource).

## Additional Information

## License

This project is licensed under the MIT License. See LICENSE.md for details.
