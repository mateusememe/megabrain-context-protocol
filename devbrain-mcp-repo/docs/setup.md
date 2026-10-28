# Setup do participante

## O que instalar

- Git
- `uv`
- um editor de código
- Node.js (LTS ou atual), só para o MCP Inspector, que roda via `npx`

Antigravity IDE ou CLI (ou outro host MCP) é opcional. Google Cloud CLI e projeto no
Google Cloud só entram no extra de deploy, que fica fora da aula. Você termina o
núcleo do workshop com o Inspector e os testes automatizados, sem login em lugar
nenhum.

## Caminho feliz

```bash
git clone https://github.com/mateusememe/megabrain-context-protocol.git
cd megabrain-context-protocol/devbrain-mcp-repo
uv python install 3.12
uv sync
uv run ruff check .
uv run pytest -q
uv run mcp dev src/devbrain_mcp/server.py
```

Antes do Inspector abrir, você deve ver o lint sem erros e os testes passando. Se o
Inspector não abrir, siga com `uv run pytest -q` e veja o
[troubleshooting](troubleshooting.md).

## Transportes

O servidor é o mesmo, qualquer que seja o transporte:

```bash
# o host inicia o processo local e conversa por stdin/stdout
uv run devbrain-mcp

# endpoint HTTP local em http://127.0.0.1:8000/mcp
uv run mcp run src/devbrain_mcp/server.py --transport streamable-http
```

stdio e Streamable HTTP são transportes; MCP é o protocolo que passa por eles. No modo
stdio, não escreva logs em stdout: o stdout pertence ao protocolo, e um `print` perdido
quebra a conexão.

## O que não fazer durante a aula

- Instalar um host específico como se fosse obrigatório.
- Criar projeto, billing ou credenciais no Google Cloud. O exercício não precisa disso.
- Tentar fazer deploy enquanto ainda está resolvendo o setup.
