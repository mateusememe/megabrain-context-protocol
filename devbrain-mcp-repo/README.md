# MCP — MegaBrain Context Protocol / DevBrain MCP

Repositório hands-on do minicurso. A trilha é **função Python -> MCP Server -> teste -> host -> Streamable HTTP -> CI/CD -> AWS**.

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

`server.py` é somente o composition root do stdio. A estrutura é hexagonal enxuta:
adaptadores MCP/HTTP/Lambda chamam casos de uso; estes chamam regras puras de domínio.

## Stack

- Python 3.12 (o MCP Python SDK suporta 3.10+; 3.12 é o baseline do workshop)
- [uv](https://docs.astral.sh/uv/) para Python, dependências, lockfile e execução
- MCP Python SDK v2 (`mcp[cli]`)
- Pydantic para modelos/saídas tipadas
- pytest + MCP `Client` in-process para testes
- AWS SAM + Lambda Function URL para o deploy didático

## Pré-requisitos

- Git
- uv
- VS Code ou editor equivalente
- Node.js (necessário apenas para o MCP Inspector)
- conta GitHub
- Opcional: Claude Code, GitHub Copilot ou Codex com suporte a MCP
- Opcional para deploy: conta AWS + AWS SAM CLI

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

## 5. Claude Code

Local:

```bash
claude mcp add devbrain -- uv run devbrain-mcp
```

Remoto:

```bash
claude mcp add --transport http devbrain https://SEU-ENDPOINT/mcp
```

## 6. GitHub Copilot

Use a configuração em `configs/copilot-project.example.json` para stdio local. Para o endpoint remoto, cadastre a URL MCP conforme o cliente/IDE utilizado.

## 7. Codex

O mesmo servidor pode ser cadastrado em qualquer host MCP compatível. Para stdio, o comando do servidor é:

```text
uv run devbrain-mcp
```

Para remoto, a URL termina em `/mcp`.

## 8. AWS com SAM

> `AuthType: NONE` existe apenas para reduzir atrito no workshop. **Não copie esse padrão para dados ou ações reais.**

```bash
uv export --no-dev --format requirements-txt --output-file requirements.txt
sam build --template-file infrastructure/template.yaml
sam deploy --guided
```

Depois conecte a Function URL (`.../mcp`) ao host escolhido.

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
```

## Referências oficiais

- MCP Python SDK v2: https://py.sdk.modelcontextprotocol.io/
- Python SDK repository: https://github.com/modelcontextprotocol/python-sdk
- MCP 2026-07-28: https://blog.modelcontextprotocol.io/posts/2026-07-28/
- uv: https://docs.astral.sh/uv/
- Anthropic launch: https://www.anthropic.com/news/model-context-protocol
- Claude Code MCP: https://docs.anthropic.com/en/docs/claude-code/mcp
- GitHub Copilot MCP: https://docs.github.com/copilot/how-tos/copilot-cli/customize-copilot/add-mcp-servers
- AWS stateless MCP: https://aws.amazon.com/blogs/architecture/mcp-went-stateless-is-your-aws-mcp-server-deployment-well-architected/
