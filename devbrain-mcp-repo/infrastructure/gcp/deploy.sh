#!/usr/bin/env bash
# Deploy manual do instrutor: o Cloud Build constrói o Dockerfile e o Cloud Run publica.
# Não precisa de Docker local.
#
# Uso:
#   export GCP_PROJECT_ID=meu-projeto
#   ./infrastructure/gcp/deploy.sh                    # serviço privado (IAM)
#   ALLOW_UNAUTHENTICATED=true ./infrastructure/gcp/deploy.sh   # URL pública, só para a demo
set -euo pipefail

source "$(dirname "$0")/config.sh"
cd "$(dirname "$0")/../.."

AUTH_FLAG="--no-allow-unauthenticated"
if [[ "${ALLOW_UNAUTHENTICATED:-false}" == "true" ]]; then
  echo "AVISO: URL pública sem autenticação. Use apenas na demo e remova depois."
  AUTH_FLAG="--allow-unauthenticated"
fi

gcloud run deploy "$SERVICE_NAME" \
  --project "$GCP_PROJECT_ID" \
  --region "$GCP_REGION" \
  --source . \
  --service-account "$RUNTIME_SA" \
  --port 8080 \
  --cpu 1 \
  --memory 512Mi \
  --min-instances 0 \
  --max-instances 3 \
  --timeout 30 \
  "$AUTH_FLAG"

URL="$(gcloud run services describe "$SERVICE_NAME" --project "$GCP_PROJECT_ID" \
  --region "$GCP_REGION" --format 'value(status.url)')"

cat <<NEXT

Endpoint MCP: $URL/mcp

Serviço privado? Abra um túnel autenticado com a sua conta gcloud:
  gcloud run services proxy $SERVICE_NAME --project $GCP_PROJECT_ID --region $GCP_REGION --port 8080
e conecte o host em http://localhost:8080/mcp
NEXT
