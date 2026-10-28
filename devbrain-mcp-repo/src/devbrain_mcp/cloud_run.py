"""Entrada Streamable HTTP para o Google Cloud Run.

O Cloud Run injeta a porta em ``PORT`` e encaminha HTTPS para o container. O serviço
do laboratório é privado por padrão (IAM); veja ``infrastructure/gcp/``.

Repare que este composition root **não** recebe repositório: na nuvem não existe o
seu código local. O mesmo servidor publica só as tools de regras puras, e os clientes
descobrem isso sozinhos em ``tools/list``. Local × remoto é uma decisão de adapters.
"""

import os

from devbrain_mcp.adapters.inbound.mcp import create_mcp_server
from devbrain_mcp.adapters.outbound.static_guidelines import StaticEngineeringGuidelines
from devbrain_mcp.application.use_cases import DevBrainUseCases

mcp = create_mcp_server(DevBrainUseCases(StaticEngineeringGuidelines()))


def main() -> None:
    """Executa o servidor stateless escutando em todas as interfaces do container."""
    mcp.run(
        transport="streamable-http",
        host="0.0.0.0",
        port=int(os.environ.get("PORT", "8080")),
        stateless_http=True,
        json_response=True,
    )


if __name__ == "__main__":
    main()
