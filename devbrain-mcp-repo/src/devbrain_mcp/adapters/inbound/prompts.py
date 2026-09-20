"""Prompts MCP: templates de workflow acionados explicitamente pelo host."""

from __future__ import annotations

from mcp.server import MCPServer

from devbrain_mcp.application.use_cases import DevBrainUseCases


def register_prompts(mcp: MCPServer, use_cases: DevBrainUseCases) -> None:
    """Registra prompts sem confundi-los com seleção autônoma de tools."""

    @mcp.prompt(name="review-feature")
    def review_feature(summary: str) -> str:
        """Prepara uma revisão de feature usando as convenções e tools DevBrain."""
        return use_cases.build_review_prompt(summary)
