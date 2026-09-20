"""Composition root e entrada stdio do DevBrain MCP."""

from devbrain_mcp.adapters.inbound.mcp import create_mcp_server
from devbrain_mcp.adapters.outbound.static_guidelines import StaticEngineeringGuidelines
from devbrain_mcp.application.use_cases import DevBrainUseCases

mcp = create_mcp_server(DevBrainUseCases(StaticEngineeringGuidelines()))


def main() -> None:
    """Executa o servidor pelo transporte stdio."""
    mcp.run()


if __name__ == "__main__":
    main()
