"""Resources MCP: contexto **somente leitura** endereçado por URI.

Diferença para tools: quem decide usar um resource é o **host ou o usuário** (anexar
ao contexto, citar com @, abrir num painel), não o modelo por conta própria. Pense
num resource como um arquivo que o host pode mostrar ao modelo; numa tool, como uma
função que o modelo pode executar.

Este arquivo mostra os dois tipos:

- **Resource estático**: URI fixa, aparece em ``resources/list``.
- **Resource template**: URI com ``{parâmetro}``, aparece em
  ``resources/templates/list``. O host preenche o parâmetro e lê a URI resultante.
"""

from __future__ import annotations

from mcp.server import MCPServer
from mcp.server.mcpserver.exceptions import ResourceError

from devbrain_mcp.application.ports import RepositoryError
from devbrain_mcp.application.use_cases import DevBrainUseCases

SERVER_GUIDE = """# Guia do servidor DevBrain

DevBrain é um servidor MCP didático: ele dá a um agente de IA as **regras de
engenharia do time** e **evidências reais do git**, sem nunca escrever nada.

## Tools (o modelo decide chamar)

| Tool | Para quê | Precisa de repositório? |
|------|----------|-------------------------|
| `inspect-branch-changes` | Ler commits e arquivos de uma branch | Sim |
| `check-pr-readiness` | Aplicar as regras R1..R5 e decidir se o PR está pronto | Não |
| `analyze-changed-files` | Classificar arquivos por área e sugerir focos de revisão | Não |

Fluxo típico: `inspect-branch-changes` → `check-pr-readiness` (com `files`,
`has_tests`, `has_docs` e `suggested_title` vindos da primeira) → `analyze-changed-files`.

## Resources (o host ou o usuário anexa)

- `repo://engineering-guidelines`: as regras R1..R6 e o porquê de cada uma.
- `devbrain://server/guide`: este guia.
- `devbrain://repository/overview`: branch atual, branches e últimos commits.
- `devbrain://repository/commits/{sha}`: um commit e os arquivos que ele tocou.

## Prompts (o usuário escolhe)

- `review-branch`: workflow completo de revisão de uma branch real.
- `review-feature`: revisão a partir de uma descrição em texto.

## Limites (de propósito)

- Somente leitura: nenhuma tool altera arquivos, branches ou remotos.
- Um único repositório, escolhido por quem roda o servidor (`DEVBRAIN_REPO_PATH`).
- Só caminhos e metadados: o DevBrain não lê o conteúdo dos arquivos.
- No Cloud Run não há repositório: só as regras puras ficam disponíveis.
"""


def register_resources(mcp: MCPServer, use_cases: DevBrainUseCases) -> None:
    """Registra recursos que um host pode listar e ler."""

    @mcp.resource(
        "repo://engineering-guidelines",
        name="engineering-guidelines",
        title="Diretrizes de engenharia (R1..R6)",
        mime_type="text/markdown",
    )
    def engineering_guidelines() -> str:
        """Regras que o DevBrain aplica a toda mudança, com o porquê de cada uma."""
        return use_cases.get_engineering_guidelines()

    @mcp.resource(
        "devbrain://server/guide",
        name="server-guide",
        title="Guia do servidor DevBrain",
        mime_type="text/markdown",
    )
    def server_guide() -> str:
        """O que cada tool, resource e prompt do DevBrain faz e quais são os limites."""
        return SERVER_GUIDE

    if not use_cases.has_repository:
        return

    @mcp.resource(
        "devbrain://repository/overview",
        name="repository-overview",
        title="Visão geral do repositório",
        mime_type="text/markdown",
    )
    def repository_overview() -> str:
        """Branch atual, branches locais e últimos commits do repositório configurado."""
        try:
            return use_cases.repository_overview()
        except RepositoryError as error:
            raise ResourceError(str(error)) from error

    @mcp.resource(
        "devbrain://repository/commits/{sha}",
        name="repository-commit",
        title="Commit do repositório",
        mime_type="application/json",
    )
    def repository_commit(sha: str) -> str:
        """Mensagem completa e arquivos alterados de um commit (SHA curto ou longo)."""
        try:
            return use_cases.commit_details(sha).model_dump_json(indent=2)
        except RepositoryError as error:
            raise ResourceError(str(error)) from error
