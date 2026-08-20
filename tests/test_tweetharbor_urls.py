from tweetharbor.extractors.urls import canonicalize_url, is_external_article


def test_canonicalize_url_removes_tracking_and_www() -> None:
    assert canonicalize_url("https://www.Example.org/path/?utm_source=x&b=2&ref=twitter") == (
        "https://example.org/path?b=2"
    )


def test_native_x_urls_are_not_external_articles() -> None:
    assert not is_external_article("https://x.com/example/status/1")
    assert is_external_article("https://example.org/article")
