"""Resources MCP: contexto read-only com URI estável."""

from __future__ import annotations

from mcp.server import MCPServer

from devbrain_mcp.application.use_cases import DevBrainUseCases


def register_resources(mcp: MCPServer, use_cases: DevBrainUseCases) -> None:
    """Registra recursos que um host pode listar e ler."""

    @mcp.resource("repo://engineering-guidelines", name="engineering-guidelines")
    def engineering_guidelines() -> str:
        """Convenções e critérios de qualidade do projeto DevBrain."""
        return use_cases.get_engineering_guidelines()
