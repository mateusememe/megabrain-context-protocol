# Referências oficiais

Links conferidos em outubro de 2026.

## MCP

- Especificação MCP 2026-07-28: https://modelcontextprotocol.io/specification/2026-07-28/
- Nota de lançamento MCP 2026-07-28: https://blog.modelcontextprotocol.io/posts/2026-07-28/
- MCP Python SDK v2: https://py.sdk.modelcontextprotocol.io/
- Repositório do Python SDK: https://github.com/modelcontextprotocol/python-sdk
- Instalação oficial (`uv add "mcp[cli]"`): https://github.com/modelcontextprotocol/python-sdk/blob/main/docs/get-started/installation.md
- Testing / Client in-process: https://github.com/modelcontextprotocol/python-sdk/blob/main/docs/get-started/testing.md
- Streamable HTTP / ASGI: https://github.com/modelcontextprotocol/python-sdk/blob/main/docs/run/asgi.md

## Python / uv

- uv documentation: https://docs.astral.sh/uv/
- Projetos com uv: https://docs.astral.sh/uv/guides/projects/
- CLI (`uv init`, `uv add`, `uv sync`, `uv run`, `uv lock`): https://docs.astral.sh/uv/reference/cli/
- Python typing: https://docs.python.org/3/library/typing.html

## História

- Anthropic, lançamento do MCP (25 nov. 2024): https://www.anthropic.com/news/model-context-protocol
- Linux Foundation, Agentic AI Foundation com MCP (9 dez. 2025): https://www.linuxfoundation.org/press/linux-foundation-announces-the-formation-of-the-agentic-ai-foundation

## Hosts

- Google Antigravity MCP (IDE, CLI e app): https://antigravity.google/docs/mcp
- Gemini CLI MCP: https://github.com/google-gemini/gemini-cli/blob/main/docs/tools/mcp-server.md
- Claude Code MCP: https://docs.anthropic.com/en/docs/claude-code/mcp
- GitHub Copilot MCP: https://docs.github.com/copilot/how-tos/copilot-cli/customize-copilot/add-mcp-servers

## Google Cloud

- Cloud Run, hospedar MCP servers: https://cloud.google.com/run/docs/host-mcp-servers
- Cloud Run, deploy a partir do código-fonte: https://cloud.google.com/run/docs/deploying-source-code
- Cloud Run, autenticar desenvolvedores: https://cloud.google.com/run/docs/authenticating/developers
- `gcloud run services proxy`: https://cloud.google.com/sdk/gcloud/reference/run/services/proxy
- Workload Identity Federation em pipelines: https://cloud.google.com/iam/docs/workload-identity-federation-with-deployment-pipelines
- `google-github-actions/auth`: https://github.com/google-github-actions/auth
- Instalação do Google Cloud CLI: https://cloud.google.com/sdk/docs/install

## Nota sobre clientes

Antigravity, Gemini CLI, Claude Code, GitHub Copilot e Codex mudam rápido. O protocolo
e o servidor do workshop continuam os mesmos, mas a tela ou o comando de configuração
de cada host pode estar diferente quando você for testar. Na dúvida, confira a
documentação do host.

No GitHub Copilot, o CLI local e o cloud agent (code review) se comportam de forma
diferente. O cloud agent só consome tools, e só mostra as que têm
`annotations.readOnlyHint=true`. Por isso o laboratório marca todas as tools como
read-only; resources e prompts ficam para os hosts que suportam.
