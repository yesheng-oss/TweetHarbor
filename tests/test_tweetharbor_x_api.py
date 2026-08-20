from datetime import UTC, datetime

import httpx
import pytest
import respx

from tweetharbor.domain.errors import TweetHarborError
from tweetharbor.domain.models import DiscoverRequest
from tweetharbor.providers.x_api import XApiProvider


def test_x_api_requires_bearer_token(monkeypatch) -> None:
    monkeypatch.delenv("X_BEARER_TOKEN", raising=False)

    with pytest.raises(TweetHarborError, match="X_BEARER_TOKEN"):
        XApiProvider().discover(DiscoverRequest(topic="AI agents"))


def test_x_api_rejects_ten_days_without_full_archive(monkeypatch) -> None:
    monkeypatch.delenv("TWEETHARBOR_X_FULL_ARCHIVE", raising=False)

    with pytest.raises(TweetHarborError, match="at most 7 days"):
        XApiProvider(bearer_token="test-token").discover(DiscoverRequest(topic="AI agents", days=10))


@respx.mock
def test_x_api_maps_official_search_response() -> None:
    route = respx.get("https://api.x.com/2/tweets/search/recent").mock(
        return_value=httpx.Response(
            200,
            json={
                "data": [
                    {
                        "id": "tweet-1",
                        "author_id": "author-1",
                        "created_at": "2026-08-18T12:00:00Z",
                        "text": "Useful agent evaluation guide",
                        "entities": {"urls": [{"expanded_url": "https://example.org/guide?utm_source=x"}]},
                        "public_metrics": {
                            "like_count": 8,
                            "retweet_count": 3,
                            "quote_count": 1,
                            "reply_count": 2,
                        },
                    }
                ],
                "includes": {"users": [{"id": "author-1", "username": "alice", "verified": True}]},
                "meta": {"result_count": 1},
            },
        )
    )
    result = XApiProvider(bearer_token="test-token").discover(
        DiscoverRequest(topic="AI agents", as_of=datetime(2026, 8, 19, tzinfo=UTC))
    )

    assert route.called
    assert result.coverage.complete is True
    assert result.posts[0].author_handle == "alice"
    assert result.posts[0].metrics.weighted == 23
    assert result.posts[0].urls == ["https://example.org/guide?utm_source=x"]
