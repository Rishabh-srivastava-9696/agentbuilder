# NOVA Azure Deployment Script

This document explains how to use the local Azure Container Apps deployment helper:

```bash
scripts/deploy_to_azure.local.sh
```

The script is intentionally local-only and ignored through `.git/info/exclude`, so secrets and machine-specific deployment behavior do not need to be committed to GitHub.

## What It Deploys

The helper can build, push, and update these NOVA services:

- `api`: FastAPI backend from `apps/api`
- `admin`: AgentBuilder admin UI from `apps/admin`
- `widget`: embeddable chat widget from `apps/widget`
- `shopify`: Shopify MCP service from `apps/shopify-mcp`
- `strapi`: Strapi admin/session service from the sibling `agentbuilder-strapi` repo
- `all`: deploys everything and reapplies API CORS/Shopify URLs after all app URLs exist

Images are built with Azure Container Registry build and deployed to Azure Container Apps.

## Prerequisites

Install and authenticate Azure CLI:

```bash
az login
az account set --subscription "<SUBSCRIPTION_ID>"
```

Azure resources expected by the script:

- Resource group
- Azure Container Registry
- Azure Container Apps environment
- MongoDB Atlas or local MongoDB reachable from Azure
- Redis, recommended for production
- Azure PostgreSQL for Strapi
- Existing Azure OpenAI deployment, if using Azure OpenAI

## Required Shell Variables

Set these before running the script:

```bash
export SUBSCRIPTION_ID="<azure-subscription-id>"
export RESOURCE_GROUP="nova-prod-rg"
export ACR_NAME="novaprodacr001"
export ACA_ENV="nova-prod-env"
```

Optional app names:

```bash
export API_APP="agentbuilder-api"
export ADMIN_APP="agentbuilder-admin"
export WIDGET_APP="agentbuilder-widget"
export SHOPIFY_APP="agentbuilder-shopify"
export STRAPI_APP="agentbuilder-strapi"
export STRAPI_ROOT="/path/to/agentbuilder-strapi"
```

If `STRAPI_ROOT` is not set, the script assumes Strapi is a sibling repo at:

```bash
../agentbuilder-strapi
```

## Local Env File

Create a local `.env.azure` file in the repo root. Do not commit it.

Example shape:

```bash
SECRET_KEY="..."
ADMIN_API_KEY="..."
SETTINGS_ENCRYPTION_KEY="..."
PII_ENCRYPTION_KEY="..."

MONGODB_URI="..."
MONGO_SYSTEM_DB="agent-builder"
MONGODB_DATABASE="agent-builder"

REDIS_URL="rediss://..."

DEFAULT_LLM_PROVIDER="azure_openai"
AZURE_OPENAI_API_KEY="..."
AZURE_OPENAI_MODEL="gpt-5.4-mini"
AZURE_OPENAI_DEPLOYMENT="gpt-5.4-mini"
AZURE_OPENAI_ENDPOINT="https://<resource>.cognitiveservices.azure.com"
AZURE_OPENAI_API_VERSION="2025-04-01-preview"

VOYAGE_API_KEY="..."
VOYAGE_BASE_URL="https://api.voyageai.com/v1"
VOYAGE_MODEL="voyage-3-large"
VOYAGE_RERANK_MODEL="rerank-2.5"

# If you are using a MongoDB Atlas Model API key instead of a native Voyage key,
# set VOYAGE_BASE_URL="https://ai.mongodb.com/v1".

API_CORS_ALLOW_ORIGINS="https://agentbuilder-api.example.com,https://agentbuilder-admin.example.com,https://agentbuilder-widget.example.com,https://agentbuilder-shopify.example.com,https://agentbuilder-strapi.example.com"

VECTOR_BACKEND="atlas"
VECTOR_INDEX_NAME="vector_index"
VECTOR_DIMENSIONS="1024"

DATABASE_HOST="<postgres-server>.postgres.database.azure.com"
DATABASE_NAME="agentbuilder_strapi"
DATABASE_USERNAME="strapiadmin"
DATABASE_PASSWORD="..."

STRAPI_API_TOKEN="..."
APP_KEYS="..."
API_TOKEN_SALT="..."
ADMIN_JWT_SECRET="..."
TRANSFER_TOKEN_SALT="..."
ENCRYPTION_KEY="..."
JWT_SECRET="..."
```

Sensitive values are written to Azure Container App secrets by the script. Non-sensitive runtime config is written as plain environment variables.

## Deploy Everything

From the `agentbuilder` repo root:

```bash
./scripts/deploy_to_azure.local.sh --service all
```

The script will:

1. Build service images in ACR.
2. Create missing Container Apps when needed.
3. Update each app image.
4. Apply secrets and environment variables.
5. Print service URLs.
6. Run quick health checks.

## Deploy One Service

```bash
./scripts/deploy_to_azure.local.sh --service api
./scripts/deploy_to_azure.local.sh --service admin
./scripts/deploy_to_azure.local.sh --service widget
./scripts/deploy_to_azure.local.sh --service shopify
./scripts/deploy_to_azure.local.sh --service strapi
```

## Reuse An Existing Image

Use this when you only want to reapply env vars or app configuration:

```bash
./scripts/deploy_to_azure.local.sh --service api --use-existing-image --tag <existing-tag>
```

The default tag format is:

```text
YYYYMMDDHHMMSS-<git-sha>
```

## Use A Different Env File

```bash
./scripts/deploy_to_azure.local.sh --service all --env-file .env.azure.production
```

## Avoid Creating Apps

Use `--no-create` when the Container Apps must already exist:

```bash
./scripts/deploy_to_azure.local.sh --service api --no-create
```

## Useful Verification Commands

```bash
az containerapp revision list \
  --name agentbuilder-api \
  --resource-group nova-prod-rg \
  -o table
```

```bash
az containerapp logs show \
  --name agentbuilder-api \
  --resource-group nova-prod-rg \
  --tail 100
```

```bash
curl -i "https://<api-fqdn>/health"
curl -i "https://<shopify-fqdn>/mcp"
curl -I "https://<strapi-fqdn>/admin"
```

## Notes

- Rotate any keys that were pasted into terminals, chats, or logs.
- Keep `.env.azure` local.
- For Cloud Shell deployment, either recreate this local script there or track a sanitized production deploy script later.
- The API deploy is run twice when using `--service all` so final CORS and Shopify MCP URLs include the generated app URLs.
- Use `API_CORS_ALLOW_ORIGINS` for the API allowlist. Use `SHOPIFY_CORS_ALLOW_ORIGINS` only when the Shopify MCP service needs a different allowlist.
