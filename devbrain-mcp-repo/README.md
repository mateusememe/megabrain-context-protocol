# MCP — MegaBrain Context Protocol / DevBrain MCP

Repositório hands-on do minicurso. A trilha é **função Python -> MCP Server -> teste -> host -> Streamable HTTP -> CI/CD -> Google Cloud Run**.

## Navegação do minicurso

| Você quer | Abra |
|---|---|
| entender a arquitetura | `docs/architecture.md` |
| seguir a implementação MCP | `src/devbrain_mcp/adapters/inbound/mcp.py` |
| ver Tools, Resources e Prompts | `src/devbrain_mcp/adapters/inbound/` |
| ver as regras sem transporte | `src/devbrain_mcp/domain/review.py` |
| trocar a fonte das diretrizes | `application/ports.py` e `adapters/outbound/` |
| preparar o notebook | `docs/setup.md` |
| conduzir a aula/failsafes | `docs/workshop.md` e `docs/troubleshooting.md` |
| conferir o que foi validado | `docs/content-review.md` |
| publicar no Google Cloud | `infrastructure/gcp/` e `docs/deploy-gcp.md` |

`server.py` é somente o composition root do stdio. A estrutura é hexagonal enxuta:
adaptadores MCP/HTTP/Cloud Run chamam casos de uso; estes chamam regras puras de domínio.

## Stack

- Python 3.12 (o MCP Python SDK suporta 3.10+; 3.12 é o baseline do workshop)
- [uv](https://docs.astral.sh/uv/) para Python, dependências, lockfile e execução
- MCP Python SDK v2 (`mcp[cli]`)
- Pydantic para modelos/saídas tipadas
- pytest + MCP `Client` in-process para testes
- Docker + Google Cloud Run (Artifact Registry, Cloud Build e Workload Identity Federation) para o deploy didático

## Pré-requisitos

- Git
- uv
- VS Code ou editor equivalente
- Node.js (necessário apenas para o MCP Inspector)
- conta GitHub
- Opcional: Google Antigravity IDE ou CLI (ou outro host MCP: Gemini CLI, Claude Code, GitHub Copilot, Codex)
- Opcional para deploy: projeto Google Cloud com billing + Google Cloud CLI (`gcloud`)

> Você não precisa instalar Python manualmente: `uv` pode instalar a versão fixada em `.python-version`.

## 1. Instalação

```bash
uv python install 3.12
uv sync
uv run pytest -q
```

Antes do evento, execute `uv lock` e versione `uv.lock` para congelar o ambiente entre instrutor, aluno e CI.

## 2. Executar local via stdio

```bash
uv run devbrain-mcp
```

Normalmente você não interage com esse processo manualmente: um host MCP o inicia como subprocesso e conversa por stdin/stdout.

## 3. MCP Inspector

```bash
uv run mcp dev src/devbrain_mcp/server.py
```

No Inspector, liste e experimente:

- Tool `check-pr-readiness`
- Tool `analyze-changed-files`
- Resource `repo://engineering-guidelines`
- Prompt `review-feature`

## 4. Servidor HTTP local

```bash
uv run mcp run src/devbrain_mcp/server.py --transport streamable-http
```

Endpoint: `http://127.0.0.1:8000/mcp`

O exemplo usa Streamable HTTP stateless, alinhado ao core MCP 2026-07-28 e
adequado a um laboratório serverless. `uv run devbrain-mcp-http` permanece como
atalho equivalente para a demo local.

## 5. Google Antigravity (IDE e CLI)

O repositório já traz a configuração de workspace em `.agents/mcp_config.json`, lida
pelo **Antigravity IDE** e pelo **Antigravity CLI** (`agy`) quando o workspace aberto é
esta pasta. Nada a instalar além do próprio Antigravity:

```json
{
  "mcpServers": {
    "devbrain": { "command": "uv", "args": ["run", "devbrain-mcp"] },
    "devbrain-cloud-run": { "serverUrl": "http://localhost:8080/mcp", "disabled": true }
  }
}
```

**Antigravity CLI**

```bash
cd devbrain-mcp-repo
agy            # dentro da sessão, digite /mcp para ver o devbrain conectado
```

Para registrar globalmente (vale em qualquer pasta), use caminho absoluto:

```bash
agy mcp add devbrain -- uv --directory "$PWD" run devbrain-mcp
agy mcp list
```

**Antigravity IDE**

1. Abra a pasta `devbrain-mcp-repo` como workspace.
2. No painel do agente: `…` → **MCP Servers** → **Manage MCP Servers** (ou **View raw config**).
3. Em **Settings → Customizations → Installed MCP Servers**, clique em **Refresh**.
4. Na primeira chamada de tool, o Antigravity pede aprovação: escolha **allow**.

Remoto (Cloud Run): com o túnel da seção 8 aberto, troque `"disabled": true` para
`false` em `devbrain-cloud-run`, ou rode `agy mcp add devbrain-cloud-run http://localhost:8080/mcp`.
Exemplo para `~/.gemini/config/mcp_config.json` em `configs/antigravity-global.example.json`.

Outros hosts usam a mesma ideia: `gemini mcp add devbrain uv run devbrain-mcp`
(Gemini CLI, exemplo em `configs/gemini-project.example.json`) ou
`claude mcp add devbrain -- uv run devbrain-mcp` (Claude Code).

## 6. GitHub Copilot

Use a configuração em `configs/copilot-project.example.json` para stdio local. Para o endpoint remoto, cadastre a URL MCP conforme o cliente/IDE utilizado.

## 7. Codex

O mesmo servidor pode ser cadastrado em qualquer host MCP compatível. Para stdio, o comando do servidor é:

```text
uv run devbrain-mcp
```

Para remoto, a URL termina em `/mcp`.

## 8. Google Cloud Run

O `Dockerfile` empacota o servidor com `uv`; o Cloud Run injeta `PORT` e o entrypoint
`devbrain-mcp-cloudrun` sobe o Streamable HTTP stateless. O serviço é **privado por
padrão** (IAM): nada de URL pública sem autenticação.

```bash
export GCP_PROJECT_ID=seu-projeto
./infrastructure/gcp/bootstrap.sh   # APIs, Artifact Registry e service account (uma vez)
./infrastructure/gcp/deploy.sh      # Cloud Build + Cloud Run, sem Docker local

# túnel autenticado com a sua conta gcloud
gcloud run services proxy devbrain-mcp --region southamerica-east1 --port 8080
```

Depois conecte o host em `http://localhost:8080/mcp`. Passo a passo, GitHub Actions
e custos em `docs/deploy-gcp.md`.

## Exercício principal

Use a seguinte mudança fictícia:

```text
Título: feat(auth): add passkey login
Arquivos: src/auth/passkey.py, src/api/auth.py
Testes: não
Docs: não
```

Peça ao agente:

> Avalie se essa feature está pronta para PR usando as ferramentas DevBrain disponíveis. Justifique com evidências.

O objetivo é o agente **descobrir** a tool adequada, chamá-la e utilizar o retorno estruturado na justificativa.

## Comandos úteis

```bash
uv sync                     # sincroniza o ambiente
uv lock                     # atualiza o lockfile
uv run pytest -q            # testes
uv run ruff check .         # lint
uv run mcp dev ...          # Inspector
uv run devbrain-mcp         # stdio
uv run mcp run src/devbrain_mcp/server.py --transport streamable-http
docker build -t devbrain-mcp . # imagem do Cloud Run
```

## Referências oficiais

- MCP Python SDK v2: https://py.sdk.modelcontextprotocol.io/
- Python SDK repository: https://github.com/modelcontextprotocol/python-sdk
- MCP 2026-07-28: https://blog.modelcontextprotocol.io/posts/2026-07-28/
- uv: https://docs.astral.sh/uv/
- Anthropic launch: https://www.anthropic.com/news/model-context-protocol
- Antigravity MCP: https://antigravity.google/docs/mcp
- Gemini CLI MCP: https://github.com/google-gemini/gemini-cli/blob/main/docs/tools/mcp-server.md
- Claude Code MCP: https://docs.anthropic.com/en/docs/claude-code/mcp
- GitHub Copilot MCP: https://docs.github.com/copilot/how-tos/copilot-cli/customize-copilot/add-mcp-servers
- Cloud Run — hospedar MCP servers: https://cloud.google.com/run/docs/host-mcp-servers
- Cloud Run — deploy a partir do código-fonte: https://cloud.google.com/run/docs/deploying-source-code
- `gcloud run services proxy`: https://cloud.google.com/sdk/gcloud/reference/run/services/proxy
- Workload Identity Federation para GitHub Actions: https://github.com/google-github-actions/auth
