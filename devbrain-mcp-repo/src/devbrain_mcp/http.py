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
