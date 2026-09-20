"""Adapter de entrada: contratos MCP para os casos de uso do DevBrain."""

from __future__ import annotations

from mcp.server import MCPServer

from devbrain_mcp.adapters.inbound.prompts import register_prompts
from devbrain_mcp.adapters.inbound.resources import register_resources
from devbrain_mcp.adapters.inbound.tools import register_tools
from devbrain_mcp.application.use_cases import DevBrainUseCases


def create_mcp_server(use_cases: DevBrainUseCases) -> MCPServer:
    """Expõe os casos de uso em MCP sem colocar regras de negócio nos decorators."""
    mcp = MCPServer("devbrain-mcp")
    register_tools(mcp, use_cases)
    register_resources(mcp, use_cases)
    register_prompts(mcp, use_cases)

    return mcp
