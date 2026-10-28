"""Adapter de entrada: monta o servidor MCP a partir dos casos de uso.

``instructions`` é enviado ao host na descoberta do servidor e muitos hosts o colocam
no contexto do modelo. É o lugar para dizer *quando* usar este servidor como um todo;
a docstring de cada tool diz quando usar aquela tool.
"""

from __future__ import annotations

from mcp.server import MCPServer

from devbrain_mcp.adapters.inbound.prompts import register_prompts
from devbrain_mcp.adapters.inbound.resources import register_resources
from devbrain_mcp.adapters.inbound.tools import register_tools
from devbrain_mcp.application.use_cases import DevBrainUseCases

SERVER_VERSION = "1.1.0"
INSTRUCTIONS = (
    "DevBrain aplica as regras de engenharia do time (R1..R6) a mudanças de código. "
    "Para avaliar uma branch real, chame inspect-branch-changes e passe as evidências "
    "para check-pr-readiness. Cite os checks pelo ID da regra. Todas as tools são "
    "somente leitura; as regras completas estão em repo://engineering-guidelines."
)


def create_mcp_server(use_cases: DevBrainUseCases) -> MCPServer:
    """Expõe os casos de uso em MCP sem colocar regras de negócio nos decorators."""
    mcp = MCPServer(
        "devbrain",
        title="DevBrain",
        version=SERVER_VERSION,
        instructions=INSTRUCTIONS,
    )
    register_tools(mcp, use_cases)
    register_resources(mcp, use_cases)
    register_prompts(mcp, use_cases)

    return mcp
