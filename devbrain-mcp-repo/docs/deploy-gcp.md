# Deploy no Google Cloud Run (extra)

Este guia é um extra para depois do curso. Nada do núcleo do workshop depende dele:
você termina o laboratório com o Inspector e os testes locais. Se quiser ver o mesmo
servidor rodando na nuvem, continue aqui.

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
| Antigravity CLI (`agy`) | host MCP no terminal | `brew install --cask antigravity-cli` |
| Antigravity IDE | host MCP no editor | `brew install --cask antigravity-ide` |
| Gemini CLI | opcional: host alternativo | `npm install -g @google/gemini-cli` |
| GitHub CLI (`gh`) | opcional: cadastrar as variables do workflow | `brew install gh` |

Você também precisa de um projeto Google Cloud com billing ativo. Configure um alerta
de orçamento antes de começar. Com `--min-instances 0`, o serviço só custa enquanto
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
repositório Docker `devbrain` e a service account de runtime `devbrain-mcp-runtime`,
sem nenhum papel. O servidor não acessa recurso algum do Google Cloud, então não
precisa de permissão.

## 3. Deploy manual

```bash
./infrastructure/gcp/deploy.sh
```

O script usa `gcloud run deploy --source .`. Quem constrói o `Dockerfile` é o Cloud
Build, então você não precisa de Docker local. O serviço sobe privado
(`--no-allow-unauthenticated`).

## 4. Conectar o host

```bash
gcloud run services proxy devbrain-mcp --region southamerica-east1 --port 8080
agy mcp add devbrain-cloud-run http://localhost:8080/mcp
```

No Antigravity IDE, troque `"disabled": true` para `false` em `devbrain-cloud-run`
(`.agents/mcp_config.json`) e clique em **Refresh** em Settings → Customizations.

O proxy autentica com a sua conta `gcloud` e expõe o serviço em `localhost`. É
autenticação remota de verdade, e ninguém precisa copiar token de lugar nenhum.

Se precisar de uma URL pública por alguns minutos:

```bash
ALLOW_UNAUTHENTICATED=true ./infrastructure/gcp/deploy.sh
```

Depois, volte para o modo privado rodando `deploy.sh` de novo, sem a variável.

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
- Workload Identity Pool `github` com um provider OIDC que só aceita o seu repositório.

No fim ele imprime os comandos `gh variable set ...`. A partir daí, cada push em `main`
que mexe no servidor roda lint e testes, constrói a imagem, manda para o Artifact
Registry e publica no Cloud Run. Nenhuma chave JSON é criada, e nada fica guardado no
GitHub.

## Limpeza

```bash
gcloud run services delete devbrain-mcp --region southamerica-east1
gcloud artifacts repositories delete devbrain --location southamerica-east1
gcloud artifacts repositories delete cloud-run-source-deploy --location southamerica-east1
```

O último repositório o próprio `deploy.sh` cria, por causa do `--source`.
