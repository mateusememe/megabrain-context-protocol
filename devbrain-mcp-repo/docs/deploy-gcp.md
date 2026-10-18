# Deploy no Google Cloud Run

Módulo do instrutor. O núcleo do workshop não depende de nada aqui: alunos terminam o
laboratório com Inspector e testes locais.

```text
LOCAL                              REMOTO
Host (Antigravity)                 Host (Antigravity)
  |                                  |
stdio                              http://localhost:8080/mcp
  |                                  |  gcloud run services proxy (IAM)
uv run devbrain-mcp                Cloud Run: devbrain-mcp-cloudrun
                                     ^
                git push -> GitHub Actions -> Artifact Registry
```

## O que instalar

| Ferramenta | Para quê | macOS |
|---|---|---|
| Google Cloud CLI (`gcloud`) | bootstrap, deploy e túnel autenticado | `brew install --cask gcloud-cli` |
| Docker | opcional: testar a imagem localmente | Docker Desktop |
| Antigravity CLI (`agy`) | host MCP da demo no terminal | `brew install --cask antigravity-cli` |
| Antigravity IDE | host MCP da demo no editor | `brew install --cask antigravity-ide` |
| Gemini CLI | opcional: host alternativo | `npm install -g @google/gemini-cli` |
| GitHub CLI (`gh`) | opcional: cadastrar as variables do workflow | `brew install gh` |

Também é preciso um projeto Google Cloud com **billing ativo**. Configure um alerta de
orçamento antes do evento. Com `--min-instances 0`, o serviço só consome enquanto
recebe requests.

```bash
gcloud auth login
gcloud config set project SEU-PROJETO
```

## 1. Testar a imagem localmente (opcional)

```bash
docker build -t devbrain-mcp .
docker run --rm -p 8080:8080 devbrain-mcp
```

Conecte o Inspector ou o host em `http://localhost:8080/mcp`.

## 2. Bootstrap do projeto (uma vez)

```bash
export GCP_PROJECT_ID=seu-projeto
export GCP_REGION=southamerica-east1          # padrão: São Paulo
./infrastructure/gcp/bootstrap.sh
```

O script habilita as APIs (Cloud Run, Artifact Registry, Cloud Build, IAM), cria o
repositório Docker `devbrain` e a service account de runtime `devbrain-mcp-runtime`
**sem papéis**: o servidor não acessa nenhum recurso do Google Cloud.

## 3. Deploy manual

```bash
./infrastructure/gcp/deploy.sh
```

Usa `gcloud run deploy --source .`: o Cloud Build constrói o `Dockerfile`, então não
é preciso ter Docker local. O serviço sobe **privado** (`--no-allow-unauthenticated`).

## 4. Conectar o host

```bash
gcloud run services proxy devbrain-mcp --region southamerica-east1 --port 8080
agy mcp add devbrain-cloud-run http://localhost:8080/mcp
```

No Antigravity IDE, troque `"disabled": true` para `false` em `devbrain-cloud-run`
(`.agents/mcp_config.json`) e clique em **Refresh** em Settings → Customizations.

O proxy autentica com a sua conta `gcloud` e expõe o serviço em `localhost`. Na aula,
isso mostra autenticação remota de verdade sem distribuir tokens.

Para uma URL pública **apenas durante a demo**:

```bash
ALLOW_UNAUTHENTICATED=true ./infrastructure/gcp/deploy.sh
```

Volte para o modo privado ao final (rode `deploy.sh` de novo sem a variável).

## 5. Deploy contínuo com GitHub Actions

`.github/workflows/deploy.yml` fica desligado até o repositório ter as variables do
GCP. Para ligar:

```bash
export GITHUB_REPO=usuario/megabrain-context-protocol
./infrastructure/gcp/bootstrap.sh
```

Com `GITHUB_REPO`, o bootstrap também cria:

- service account `github-deployer` com `run.admin`, `artifactregistry.writer` no
  repositório e `iam.serviceAccountUser` só na SA de runtime;
- Workload Identity Pool `github` + provider OIDC restrito ao seu repositório.

No fim ele imprime os comandos `gh variable set ...`. Depois disso, cada push em
`main` que altera o servidor roda lint e testes, constrói a imagem, envia ao Artifact
Registry e publica no Cloud Run. Nenhuma chave JSON é criada ou guardada no GitHub.

## Limpeza depois do evento

```bash
gcloud run services delete devbrain-mcp --region southamerica-east1
gcloud artifacts repositories delete devbrain --location southamerica-east1
gcloud artifacts repositories delete cloud-run-source-deploy --location southamerica-east1
```

O último repositório é criado automaticamente pelo `deploy.sh` (`--source`).
