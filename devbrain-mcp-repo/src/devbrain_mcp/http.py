"""Entrada Streamable HTTP local: o mesmo servidor, agora atrás de uma URL.

Útil para mostrar o protocolo "cru" com curl e para conectar vários hosts ao mesmo
processo. ``stateless_http`` + ``json_response``: cada POST em ``/mcp`` carrega tudo
de que precisa e recebe um JSON simples de volta, sem sessão nem stream SSE.
"""

from devbrain_mcp.server import mcp


def main() -> None:
    """Executa o servidor via Streamable HTTP em modo stateless."""
    mcp.run(
        transport="streamable-http",
        host="127.0.0.1",
        port=8000,
        stateless_http=True,
        json_response=True,
    )


if __name__ == "__main__":
    main()
