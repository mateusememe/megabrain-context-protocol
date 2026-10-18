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
