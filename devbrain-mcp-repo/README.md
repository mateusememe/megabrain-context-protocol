# DevBrain MCP

Repositório hands-on do minicurso MCP: MegaBrain Context Protocol. O caminho é
função Python -> MCP Server -> teste -> host -> Streamable HTTP. CI/CD e Google Cloud
Run ficam como extra, para depois do curso (seção 8).

## Por onde começar

| Você quer | Abra |
|---|---|
| começar do zero e testar tudo | `docs/roteiro-de-testes.md` |
| entender cada arquivo e cada conceito MCP | `docs/tour-do-codigo.md` |
| entender a arquitetura | `docs/architecture.md` |
| seguir a implementação MCP | `src/devbrain_mcp/adapters/inbound/mcp.py` |
| ver Tools, Resources e Prompts | `src/devbrain_mcp/adapters/inbound/` |
| ver as regras sem transporte | `src/devbrain_mcp/domain/review.py` |
| trocar a fonte das diretrizes | `application/ports.py` e `adapters/outbound/` |
| ver as defesas de segurança | `adapters/outbound/git_repository.py` |
| preparar o notebook | `docs/setup.md` |
| resolver um problema | `docs/troubleshooting.md` |
| publicar no Google Cloud (extra) | `infrastructure/gcp/` e `docs/deploy-gcp.md` |

O `server.py` só monta o servidor para stdio. A estrutura é hexagonal e pequena: os
adaptadores (MCP, HTTP, Cloud Run) chamam casos de uso, e os casos de uso chamam regras
puras de domínio.

## Stack

- Python 3.12 (o MCP Python SDK aceita 3.10+, mas o workshop usa 3.12)
- [uv](https://docs.astral.sh/uv/) para Python, dependências, lockfile e execução
- MCP Python SDK v2 (`mcp[cli]`)
- Pydantic para os modelos e as saídas tipadas
- pytest com o `Client` MCP in-process
- Docker e Google Cloud Run (Artifact Registry, Cloud Build e Workload Identity
  Federation), só no extra de deploy

## Pré-requisitos

- Git
- uv
- VS Code ou outro editor
- Node.js, só para o MCP Inspector
- conta no GitHub
- opcional: Google Antigravity IDE ou CLI, ou outro host MCP (Gemini CLI, Claude Code,
  GitHub Copilot, Codex)
- opcional, para o deploy: projeto Google Cloud com billing e o Google Cloud CLI
  (`gcloud`)

> Não precisa instalar Python à mão: o `uv` instala a versão fixada em
> `.python-version`.

## 1. Instalação

```bash
uv python install 3.12
uv sync
uv run pytest -q
```

O `uv.lock` já está versionado, então você, o instrutor e o CI rodam com as mesmas
versões.

## 2. Rodar local via stdio

```bash
uv run devbrain-mcp
```

Normalmente você não conversa com esse processo direto. Quem faz isso é o host MCP: ele
inicia o servidor como subprocesso e fala com ele por stdin/stdout.

## 3. MCP Inspector

```bash
uv run mcp dev src/devbrain_mcp/server.py
```

No Inspector, liste e experimente:

| Primitiva | Nome | O que faz |
|---|---|---|
| Tool | `inspect-branch-changes` | lê do git os commits e arquivos de uma branch (somente leitura) |
| Tool | `check-pr-readiness` | aplica as regras R1..R5 e diz se o PR está pronto |
| Tool | `analyze-changed-files` | classifica arquivos por área e sugere onde focar a revisão |
| Resource | `repo://engineering-guidelines` | as regras R1..R6 e o porquê de cada uma |
| Resource | `devbrain://server/guide` | o que o servidor faz e os limites dele |
| Resource | `devbrain://repository/overview` | branch atual, branches e últimos commits |
| Template | `devbrain://repository/commits/{sha}` | um commit e os arquivos que ele tocou |
| Prompt | `review-branch` | revisão completa de uma branch real |
| Prompt | `review-feature` | revisão a partir de uma descrição em texto |

O DevBrain lê o repositório indicado em `DEVBRAIN_REPO_PATH`. Sem a variável, ele usa
o repositório git da pasta atual. Para apontar para outro repositório, gere configs
com `env` explícito:

```bash
./scripts/preparar_demo.sh ~/caminho/do/seu-repo
```

O script imprime os comandos do Inspector, do Claude Code e do Antigravity já
apontando para esse repositório. As tools de repositório só existem localmente; no
Cloud Run, só as regras puras são publicadas.

## 4. Servidor HTTP local

```bash
uv run mcp run src/devbrain_mcp/server.py --transport streamable-http
```

Endpoint: `http://127.0.0.1:8000/mcp`

O servidor usa Streamable HTTP stateless, como pede o core MCP 2026-07-28, o que
combina com rodar em serverless. `uv run devbrain-mcp-http` faz a mesma coisa.

## 5. Google Antigravity (IDE e CLI)

O repositório já traz a configuração de workspace em `.agents/mcp_config.json`. O
Antigravity IDE e o Antigravity CLI (`agy`) leem esse arquivo quando o workspace é esta
pasta. Não precisa instalar mais nada além do próprio Antigravity:

```json
{
  "mcpServers": {
    "devbrain": { "command": "uv", "args": ["run", "devbrain-mcp"] },
    "devbrain-cloud-run": { "serverUrl": "http://localhost:8080/mcp", "disabled": true }
  }
}
```

### Antigravity CLI

```bash
cd devbrain-mcp-repo
agy            # dentro da sessão, digite /mcp para ver o devbrain conectado
```

Para registrar globalmente (vale em qualquer pasta), use caminho absoluto:

```bash
agy mcp add devbrain -- uv --directory "$PWD" run devbrain-mcp
agy mcp list
```

### Antigravity IDE

1. Abra a pasta `devbrain-mcp-repo` como workspace.
2. No painel do agente, vá em `…` → MCP Servers → Manage MCP Servers (ou View raw
   config).
3. Em Settings → Customizations → Installed MCP Servers, clique em Refresh.
4. Na primeira chamada de tool, o Antigravity pede aprovação. Escolha allow.

Para usar o servidor remoto (extra de Cloud Run): com o túnel da seção 8 aberto, troque
`"disabled": true` para `false` em `devbrain-cloud-run`, ou rode
`agy mcp add devbrain-cloud-run http://localhost:8080/mcp`. Há um exemplo de config
global em `configs/antigravity-global.example.json`.

Outros hosts seguem a mesma ideia. No Gemini CLI, `gemini mcp add devbrain uv run
devbrain-mcp` (exemplo em `configs/gemini-project.example.json`). O Claude Code já lê o
`.mcp.json` desta pasta; o passo a passo está em `docs/roteiro-de-testes.md`.

## 6. GitHub Copilot

Use `configs/copilot-project.example.json` para stdio local. Para o endpoint remoto,
cadastre a URL MCP do jeito que o seu cliente ou IDE pede.

## 7. Codex e outros hosts

Qualquer host MCP compatível aceita o mesmo servidor. Para stdio, o comando é:

```text
uv run devbrain-mcp
```

Para remoto, a URL termina em `/mcp`.

## 8. Google Cloud Run (extra)

> O deploy não faz parte da aula. Use esta seção depois, se quiser publicar o
> servidor.

O `Dockerfile` empacota o servidor com `uv`. O Cloud Run injeta a variável `PORT`, e o
entrypoint `devbrain-mcp-cloudrun` sobe o Streamable HTTP stateless. O serviço é
privado por padrão (IAM): nada de URL pública sem autenticação.

```bash
export GCP_PROJECT_ID=seu-projeto
./infrastructure/gcp/bootstrap.sh   # APIs, Artifact Registry e service account (uma vez)
./infrastructure/gcp/deploy.sh      # Cloud Build + Cloud Run, sem Docker local

# túnel autenticado com a sua conta gcloud
gcloud run services proxy devbrain-mcp --region southamerica-east1 --port 8080
```

Depois conecte o host em `http://localhost:8080/mcp`. GitHub Actions, custos e o
passo a passo completo estão em `docs/deploy-gcp.md`.

## Exercício principal

### Num repositório seu

Aponte o DevBrain para um repositório seu e pergunte ao agente se uma branch está
pronta para PR. Para ver o mesmo fluxo sem LLM, só com o protocolo:

```bash
uv run python scripts/demo_sem_llm.py ~/caminho/do/seu-repo main sua-branch
```

### Com uma mudança fictícia

```text
Título: feat(auth): add passkey login
Arquivos: src/auth/passkey.py, src/api/auth.py
Testes: não
Docs: não
```

Peça ao agente:

> Avalie se essa feature está pronta para PR usando as ferramentas DevBrain
> disponíveis. Justifique com evidências.

Não diga qual tool usar. A graça está em ver o agente descobrir a tool certa, chamar e
usar o retorno estruturado na justificativa.

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
- Repositório do Python SDK: https://github.com/modelcontextprotocol/python-sdk
- MCP 2026-07-28: https://blog.modelcontextprotocol.io/posts/2026-07-28/
- uv: https://docs.astral.sh/uv/
- Lançamento do MCP pela Anthropic: https://www.anthropic.com/news/model-context-protocol
- Antigravity MCP: https://antigravity.google/docs/mcp
- Gemini CLI MCP: https://github.com/google-gemini/gemini-cli/blob/main/docs/tools/mcp-server.md
- Claude Code MCP: https://docs.anthropic.com/en/docs/claude-code/mcp
- GitHub Copilot MCP: https://docs.github.com/copilot/how-tos/copilot-cli/customize-copilot/add-mcp-servers
- Cloud Run, hospedar MCP servers: https://cloud.google.com/run/docs/host-mcp-servers
- Cloud Run, deploy a partir do código-fonte: https://cloud.google.com/run/docs/deploying-source-code
- `gcloud run services proxy`: https://cloud.google.com/sdk/gcloud/reference/run/services/proxy
- Workload Identity Federation para GitHub Actions: https://github.com/google-github-actions/auth
