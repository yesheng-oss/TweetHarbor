from datetime import UTC, datetime

import pytest

from tweetharbor.application.service import DiscoveryService
from tweetharbor.domain.errors import TweetHarborError
from tweetharbor.domain.models import DiscoverRequest
from tweetharbor.output.renderers import render_json, render_markdown
from tweetharbor.providers.base import ProviderResponse
from tweetharbor.providers.fixture import FixtureProvider
from tweetharbor.storage.database import Database

AS_OF = datetime(2026, 8, 19, tzinfo=UTC)


def build_service(tmp_path) -> DiscoveryService:
    return DiscoveryService({"fixture": FixtureProvider()}, Database(tmp_path / "harbor.db"))


def test_fixture_discovers_and_deduplicates_articles(tmp_path) -> None:
    result = build_service(tmp_path).discover(
        DiscoverRequest(topic="AI Agent", days=10, provider="fixture", as_of=AS_OF)
    )

    assert result.status == "ok"
    assert result.coverage.complete is True
    assert len(result.items) == 3
    evaluations = next(item for item in result.items if "agent-evals" in str(item.canonical_url))
    assert len(evaluations.evidence_posts) == 2
    assert len(evaluations.canonical_aliases) == 2
    assert evaluations.score is not None
    assert evaluations.score.version == "article-v1"


def test_uncertain_date_is_opt_in(tmp_path) -> None:
    service = build_service(tmp_path)
    excluded = service.discover(
        DiscoverRequest(topic="AI Agent", days=10, provider="fixture", as_of=AS_OF)
    )
    included = service.discover(
        DiscoverRequest(
            topic="AI Agent",
            days=10,
            provider="fixture",
            as_of=AS_OF,
            include_uncertain_dates=True,
        )
    )

    assert len(included.items) == len(excluded.items) + 1
    assert any(item.eligibility == "uncertain_date" for item in included.items)


def test_require_complete_rejects_partial_provider_coverage(tmp_path) -> None:
    response = FixtureProvider().discover(DiscoverRequest(topic="AI agent"))
    response.coverage.complete = False
    response.coverage.status = "partial"
    response.coverage.degraded_reasons = ["test-only partial coverage"]

    class PartialProvider:
        def discover(self, request: DiscoverRequest) -> ProviderResponse:
            return response

    service = DiscoveryService({"partial": PartialProvider()}, Database(tmp_path / "test.db"))
    with pytest.raises(TweetHarborError, match="complete coverage"):
        service.discover(DiscoverRequest(topic="AI agent", provider="partial", require_complete=True))


def test_json_and_markdown_use_the_same_rank_order(tmp_path) -> None:
    result = build_service(tmp_path).discover(
        DiscoverRequest(topic="AI Agent", days=10, provider="fixture", as_of=AS_OF)
    )

    payload = render_json(result)
    markdown = render_markdown(result)
    assert '"schema_version": "1.0"' in payload
    assert "# TweetHarbor: AI Agent" in markdown
    assert "A Practical Guide to Agent Evaluations" in markdown
