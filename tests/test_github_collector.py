from starscout.collectors.github import GitHubCollector


def test_build_query() -> None:
    query = GitHubCollector._build_query("AI Agent")
    assert "AI Agent" in query
    assert "in:name,description,topics" in query
    assert "stars:>=10" in query
