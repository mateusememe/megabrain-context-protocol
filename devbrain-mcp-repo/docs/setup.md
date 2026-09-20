# Setup do participante

## Pré-requisitos mínimos

- Git;
- `uv`;
- editor de código;
- Node.js LTS ou atual **somente** para o MCP Inspector (`mcp dev` usa npx);
- conta GitHub para os exercícios de CI/CD.

Claude Code, GitHub Copilot, Codex, AWS SAM CLI e conta AWS são opcionais. O núcleo
do workshop termina usando o Inspector e os testes automatizados, sem login externo.

## Golden path

```bash
git clone SEU-REPOSITORIO
cd devbrain-mcp
uv python install 3.12
uv sync
uv run ruff check .
uv run pytest -q
uv run mcp dev src/devbrain_mcp/server.py
```

Saída esperada antes do Inspector: lint sem erros e testes verdes. Se o Inspector
não abrir, a aula continua com `uv run pytest -q`; veja `troubleshooting.md`.

## Transportes

O servidor MCP não muda quando o transporte muda:

```bash
# Host inicia o processo local e conversa por stdin/stdout
uv run devbrain-mcp

# Endpoint HTTP local em http://127.0.0.1:8000/mcp
uv run mcp run src/devbrain_mcp/server.py --transport streamable-http
```

`stdio` e Streamable HTTP são transportes; MCP é o protocolo. Evite imprimir logs
em stdout no modo stdio, pois stdout pertence ao protocolo.

## Não faça no núcleo

- não instale um host específico como dependência da aula;
- não crie credenciais AWS para concluir o exercício;
- não execute deploy durante o troubleshooting de setup.
