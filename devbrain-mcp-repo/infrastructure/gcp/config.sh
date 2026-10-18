# Configuração compartilhada pelos scripts GCP do laboratório.
# Sobrescreva qualquer valor exportando a variável antes de rodar o script.

: "${GCP_PROJECT_ID:?defina GCP_PROJECT_ID (ex.: export GCP_PROJECT_ID=devbrain-devfest)}"
GCP_REGION="${GCP_REGION:-southamerica-east1}"
SERVICE_NAME="${SERVICE_NAME:-devbrain-mcp}"
ARTIFACT_REPO="${ARTIFACT_REPO:-devbrain}"
RUNTIME_SA_NAME="${RUNTIME_SA_NAME:-devbrain-mcp-runtime}"
DEPLOY_SA_NAME="${DEPLOY_SA_NAME:-github-deployer}"
WIF_POOL="${WIF_POOL:-github}"
WIF_PROVIDER="${WIF_PROVIDER:-github-oidc}"

RUNTIME_SA="${RUNTIME_SA_NAME}@${GCP_PROJECT_ID}.iam.gserviceaccount.com"
DEPLOY_SA="${DEPLOY_SA_NAME}@${GCP_PROJECT_ID}.iam.gserviceaccount.com"
