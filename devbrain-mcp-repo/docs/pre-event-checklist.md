# Checklist pré-evento

## Gate técnico (instrutor)

- [ ] `uv sync`
- [ ] `uv run ruff check .`
- [ ] `uv run pytest -q`
- [ ] `uv run mcp dev src/devbrain_mcp/server.py`
- [ ] `uv run mcp run src/devbrain_mcp/server.py --transport streamable-http`
- [ ] Inspector lista duas Tools, um Resource e um Prompt
- [ ] smoke de um host real, se ele for usado na demo
- [ ] `sam validate`/deploy executados apenas na conta do instrutor

## Gate de conteúdo

- [ ] deck usa Model Context Protocol após o hook “MegaBrain”;
- [ ] deck e guias usam SDK Python v2 / `MCPServer`;
- [ ] não há URL antiga `ts.sdk.modelcontextprotocol.io`;
- [ ] slide de segurança afirma que LLM não é boundary de segurança;
- [ ] slides explicam quando **não** usar MCP;
- [ ] QR/repositório, ZIP e PDF correspondem ao commit final.

## Gate operacional

- [ ] repositório e ZIP disponíveis offline;
- [ ] screenshots/saídas esperadas do Inspector disponíveis;
- [ ] tags `starter`, `checkpoint-1`, `checkpoint-2` e `final` publicadas;
- [ ] demo sem host e sem AWS ensaiada;
- [ ] adaptador de energia, rede e plano de contingência revisados.
