"""Tools MCP: ações que o **modelo** decide chamar.

Como o modelo decide? Ele só lê três coisas que este arquivo publica em ``tools/list``:

1. ``name`` e ``title``: curtos, em kebab-case, orientados a intenção;
2. ``description``: a docstring da função. É *prompt engineering*: diga quando usar,
   o que volta e qual tool chamar depois;
3. ``inputSchema``: gerado dos type hints. ``Annotated[..., Field(description=...)]``
   vira a descrição de cada argumento que o modelo vê.

O retorno é um modelo Pydantic, então o SDK também publica ``outputSchema`` e devolve
``structuredContent`` (JSON validável) além do texto. Hosts como o Claude Code validam
a resposta contra o schema. Se o contrato mentir, a chamada falha.

Erros: ``ToolError`` vira um resultado com ``isError: true`` e a **mensagem chega ao
modelo**, que pode corrigir os argumentos e tentar de novo. Qualquer outra exceção é
tratada como crash e o modelo vê só "Error executing tool".
"""

from __future__ import annotations

from collections.abc import Callable
from typing import Annotated

from mcp.server import MCPServer
from mcp.server.mcpserver.exceptions import ToolError
from mcp.types import ToolAnnotations
from pydantic import Field

from devbrain_mcp.application.ports import RepositoryError
from devbrain_mcp.application.use_cases import DevBrainUseCases
from devbrain_mcp.domain.changes import BranchChanges
from devbrain_mcp.domain.review import ChangedFilesAnalysis, PRReadiness

# Dicas para o host decidir quanta confirmação pedir. Nenhuma tool do DevBrain escreve
# nada (readOnly) e o resultado só depende dos argumentos e do repositório (closed world).
READ_ONLY_LOCAL_TOOL = ToolAnnotations(read_only_hint=True, open_world_hint=False)

FilePaths = Annotated[
    list[str],
    Field(description="Caminhos relativos à raiz do repositório, ex.: src/auth/passkey.py."),
]


def as_tool_error[T](action: Callable[[], T]) -> T:
    """Converte erros previstos do domínio em ``ToolError`` para o modelo ler."""
    try:
        return action()
    except (ValueError, RepositoryError) as error:
        raise ToolError(str(error)) from error


def register_tools(mcp: MCPServer, use_cases: DevBrainUseCases) -> None:
    """Registra as tools; as de repositório só existem se houver repositório."""

    @mcp.tool(
        name="check-pr-readiness",
        title="Checar prontidão do PR",
        annotations=READ_ONLY_LOCAL_TOOL,
    )
    def check_pr_readiness(
        title: Annotated[str, Field(description="Título proposto para o pull request.")],
        changed_files: FilePaths,
        has_tests: Annotated[
            bool, Field(description="true se a mudança inclui testes automatizados.")
        ],
        has_docs: Annotated[
            bool, Field(description="true se a mudança atualiza documentação.")
        ] = False,
    ) -> PRReadiness:
        """Avalia se uma mudança está pronta para abrir um pull request.

        Aplica as regras R1..R5 de repo://engineering-guidelines e devolve a decisão
        (ready), o risco, os bloqueios, as recomendações e um check por regra com a
        evidência. Use depois de inspect-branch-changes para avaliar uma branch real.
        """
        return as_tool_error(
            lambda: use_cases.check_pr_readiness(title, changed_files, has_tests, has_docs)
        )

    @mcp.tool(
        name="analyze-changed-files",
        title="Classificar arquivos alterados",
        annotations=READ_ONLY_LOCAL_TOOL,
    )
    def analyze_changed_files(files: FilePaths) -> ChangedFilesAnalysis:
        """Classifica arquivos alterados por área técnica e sugere focos de revisão.

        Útil para decidir quem deve revisar (segurança, API, infraestrutura) e o que
        olhar primeiro. Só olha os caminhos; não lê o conteúdo dos arquivos.
        """
        return as_tool_error(lambda: use_cases.analyze_changed_files(files))

    if not use_cases.has_repository:
        return

    @mcp.tool(
        name="inspect-branch-changes",
        title="Inspecionar mudanças da branch",
        annotations=READ_ONLY_LOCAL_TOOL,
    )
    def inspect_branch_changes(
        base: Annotated[
            str, Field(description="Branch de destino do PR, ex.: main ou develop.")
        ] = "main",
        head: Annotated[
            str, Field(description="Branch ou commit a avaliar. HEAD = branch atual.")
        ] = "HEAD",
    ) -> BranchChanges:
        """Lê do git os commits e arquivos que um PR de head para base traria.

        Somente leitura, no repositório configurado por quem roda o servidor. Devolve
        evidências prontas para check-pr-readiness: lista de arquivos, has_tests,
        has_docs, dependências alteradas, commits fora do padrão e um título sugerido.
        """
        return as_tool_error(lambda: use_cases.inspect_branch_changes(base, head))
