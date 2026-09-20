# Revisão técnica e de conteúdo — 20 set. 2026

## Validado localmente

- `uv run ruff check .` e `uv run pytest -q`: verificam lint, cinco testes e a
  descoberta/execução MCP in-process.
- `uv run mcp run src/devbrain_mcp/server.py --transport streamable-http` iniciou
  em `127.0.0.1:8000`; uma descoberta `server/discover` da spec `2026-07-28`
  respondeu `200`.
- As duas tools continuam retornando schema e conteúdo estruturado; o caso de
  passkey retorna risco alto e não pronto quando não há testes.
- O uso de `MCPServer`, `Client(mcp)`, `mcp dev`, type hints, Pydantic e
  Streamable HTTP está coerente com a linha estável v2 do SDK oficial.
- As configurações de Claude e Copilot usam stdio com `uv run devbrain-mcp`.

## Ajustes aplicados

- Separação hexagonal enxuta e teste direto das regras de domínio.
- Anotações `read_only_hint=True` nas tools. Isso torna explícito para hosts que
  essas capabilities não alteram estado e atende ao requisito de tool annotations
  de clientes como Copilot code review.
- `uv.lock` foi gerado após resolver as dependências; ele deve acompanhar tanto o
  repositório canônico quanto o pacote distribuído.

## Limites desta validação

- O SAM CLI não está instalado neste ambiente; deploy Lambda, credenciais OIDC e um
  host real não foram executados. Eles exigem conta/configuração externa e não são
  provados pelos testes locais.
- `AuthType: NONE` e CORS aberto continuam aceitáveis somente no laboratório. Não
  publicar com esses valores fora dele.
- O conteúdo do chat compartilhado indicado como origem não ficou disponível para
  leitura pública nesta revisão; por isso não há afirmação de que o material está
  fiel a ele. Exporte ou cole a conversa para uma comparação linha a linha.
- O PPTX recebeu referências atualizadas e speaker notes; o PDF de 45 páginas foi
  renderizado localmente a partir dele e os ZIPs foram reconstruídos. Esses
  artefatos editoriais ficam fora do controle de versão; mantenha a checagem em
  projetor como gate pré-evento.
