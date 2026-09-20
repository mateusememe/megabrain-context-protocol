"""Tools MCP: capabilities pequenas, read-only e orientadas a intenção."""

from __future__ import annotations

from mcp.server import MCPServer
from mcp.types import ToolAnnotations

from devbrain_mcp.application.use_cases import DevBrainUseCases
from devbrain_mcp.domain.review import ChangedFilesAnalysis, PRReadiness

READ_ONLY_LOCAL_TOOL = ToolAnnotations(read_only_hint=True, open_world_hint=False)


def register_tools(mcp: MCPServer, use_cases: DevBrainUseCases) -> None:
    """Registra capabilities sem misturar regras de negócio nos decorators."""

    @mcp.tool(name="check-pr-readiness", annotations=READ_ONLY_LOCAL_TOOL)
    def check_pr_readiness(
        title: str,
        changed_files: list[str],
        has_tests: bool,
        has_docs: bool = False,
    ) -> PRReadiness:
        """Avalia se uma mudança está pronta para abrir um pull request.

        Aplica as regras de engenharia do DevBrain.
        """
        return use_cases.check_pr_readiness(title, changed_files, has_tests, has_docs)

    @mcp.tool(name="analyze-changed-files", annotations=READ_ONLY_LOCAL_TOOL)
    def analyze_changed_files(files: list[str]) -> ChangedFilesAnalysis:
        """Classifica arquivos alterados por área técnica e sugere focos de revisão."""
        return use_cases.analyze_changed_files(files)
