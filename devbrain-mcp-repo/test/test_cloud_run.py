from devbrain_mcp import cloud_run


def test_cloud_run_listens_on_injected_port(monkeypatch) -> None:
    calls: list[dict] = []
    monkeypatch.setenv("PORT", "9090")
    monkeypatch.setattr(cloud_run.mcp, "run", lambda **kwargs: calls.append(kwargs))

    cloud_run.main()

    assert calls == [
        {
            "transport": "streamable-http",
            "host": "0.0.0.0",
            "port": 9090,
            "stateless_http": True,
            "json_response": True,
        }
    ]


async def test_cloud_run_server_has_no_local_repository() -> None:
    from mcp import Client

    async with Client(cloud_run.mcp, raise_exceptions=True) as client:
        tools = await client.list_tools()

    assert "inspect-branch-changes" not in {tool.name for tool in tools.tools}
