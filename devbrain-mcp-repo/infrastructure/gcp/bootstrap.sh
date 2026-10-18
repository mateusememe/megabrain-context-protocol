#!/usr/bin/env bash
# Prepara um projeto Google Cloud para o DevBrain MCP. Pode ser executado de novo:
# cada recurso só é criado quando ainda não existe.
#
# Uso:
#   export GCP_PROJECT_ID=meu-projeto
#   export GITHUB_REPO=usuario/megabrain-context-protocol   # opcional: habilita o deploy via GitHub Actions
#   ./infrastructure/gcp/bootstrap.sh
set -euo pipefail

source "$(dirname "$0")/config.sh"
GITHUB_REPO="${GITHUB_REPO:-}"

gcloud config set project "$GCP_PROJECT_ID" >/dev/null
PROJECT_NUMBER="$(gcloud projects describe "$GCP_PROJECT_ID" --format='value(projectNumber)')"

echo "==> Habilitando APIs"
gcloud services enable \
  run.googleapis.com \
  artifactregistry.googleapis.com \
  cloudbuild.googleapis.com \
  iam.googleapis.com \
  iamcredentials.googleapis.com \
  sts.googleapis.com

echo "==> Artifact Registry: $ARTIFACT_REPO ($GCP_REGION)"
gcloud artifacts repositories describe "$ARTIFACT_REPO" --location "$GCP_REGION" >/dev/null 2>&1 ||
  gcloud artifacts repositories create "$ARTIFACT_REPO" \
    --repository-format docker \
    --location "$GCP_REGION" \
    --description "Imagens do DevBrain MCP"

echo "==> Service account de runtime (sem papéis: o servidor não acessa nada no GCP)"
gcloud iam service-accounts describe "$RUNTIME_SA" >/dev/null 2>&1 ||
  gcloud iam service-accounts create "$RUNTIME_SA_NAME" --display-name "DevBrain MCP runtime"

if [[ -z "$GITHUB_REPO" ]]; then
  echo "==> GITHUB_REPO não definido: pulando Workload Identity Federation."
  echo "    O deploy manual já funciona: ./infrastructure/gcp/deploy.sh"
  exit 0
fi

echo "==> Service account de deploy usada pelo GitHub Actions"
gcloud iam service-accounts describe "$DEPLOY_SA" >/dev/null 2>&1 ||
  gcloud iam service-accounts create "$DEPLOY_SA_NAME" --display-name "GitHub Actions deployer"

gcloud projects add-iam-policy-binding "$GCP_PROJECT_ID" \
  --member "serviceAccount:$DEPLOY_SA" --role roles/run.admin --condition None >/dev/null
gcloud artifacts repositories add-iam-policy-binding "$ARTIFACT_REPO" \
  --location "$GCP_REGION" \
  --member "serviceAccount:$DEPLOY_SA" --role roles/artifactregistry.writer >/dev/null
gcloud iam service-accounts add-iam-policy-binding "$RUNTIME_SA" \
  --member "serviceAccount:$DEPLOY_SA" --role roles/iam.serviceAccountUser >/dev/null

echo "==> Workload Identity Federation para $GITHUB_REPO (sem chaves JSON)"
gcloud iam workload-identity-pools describe "$WIF_POOL" --location global >/dev/null 2>&1 ||
  gcloud iam workload-identity-pools create "$WIF_POOL" \
    --location global --display-name "GitHub Actions"

gcloud iam workload-identity-pools providers describe "$WIF_PROVIDER" \
  --location global --workload-identity-pool "$WIF_POOL" >/dev/null 2>&1 ||
  gcloud iam workload-identity-pools providers create-oidc "$WIF_PROVIDER" \
    --location global \
    --workload-identity-pool "$WIF_POOL" \
    --display-name "GitHub OIDC" \
    --issuer-uri "https://token.actions.githubusercontent.com" \
    --attribute-mapping "google.subject=assertion.sub,attribute.repository=assertion.repository" \
    --attribute-condition "assertion.repository == '$GITHUB_REPO'"

POOL_ID="projects/$PROJECT_NUMBER/locations/global/workloadIdentityPools/$WIF_POOL"
gcloud iam service-accounts add-iam-policy-binding "$DEPLOY_SA" \
  --role roles/iam.workloadIdentityUser \
  --member "principalSet://iam.googleapis.com/$POOL_ID/attribute.repository/$GITHUB_REPO" >/dev/null

cat <<VARS

Pronto. Cadastre estas *variables* (não são segredos) no repositório GitHub:

gh variable set GCP_PROJECT_ID --repo $GITHUB_REPO --body "$GCP_PROJECT_ID"
gh variable set GCP_REGION --repo $GITHUB_REPO --body "$GCP_REGION"
gh variable set GCP_WORKLOAD_IDENTITY_PROVIDER --repo $GITHUB_REPO --body "$POOL_ID/providers/$WIF_PROVIDER"
gh variable set GCP_DEPLOY_SERVICE_ACCOUNT --repo $GITHUB_REPO --body "$DEPLOY_SA"
gh variable set GCP_RUNTIME_SERVICE_ACCOUNT --repo $GITHUB_REPO --body "$RUNTIME_SA"
VARS
