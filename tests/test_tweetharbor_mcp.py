from tweetharbor.mcp_server import SERVER_INSTRUCTIONS, create_server


def test_mcp_server_exposes_stdio_runtime(tmp_path) -> None:
    server = create_server(tmp_path / "harbor.db")

    assert "10-day result" in SERVER_INSTRUCTIONS
    assert server.name == "TweetHarbor"
    assert callable(server.run)
