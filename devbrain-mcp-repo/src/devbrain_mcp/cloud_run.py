"""Entrada Streamable HTTP para o Google Cloud Run.

O Cloud Run injeta a porta em ``PORT`` e encaminha HTTPS para o container. O serviço
do laboratório é privado por padrão (IAM); veja ``infrastructure/gcp/``.
"""

import os

from devbrain_mcp.server import mcp


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
