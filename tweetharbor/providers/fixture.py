from __future__ import annotations

import json
from datetime import UTC, datetime, timedelta
from importlib.resources import files

from tweetharbor.domain.models import Coverage, CoverageStatus, DiscoverRequest, EvidencePost
from tweetharbor.providers.base import ProviderResponse


class FixtureProvider:
    """Deterministic provider used for local demos and contract tests."""

    name = "fixture"

    def discover(self, request: DiscoverRequest) -> ProviderResponse:
        payload = json.loads(
            files("tweetharbor.fixtures").joinpath("ai_agent_posts.json").read_text(encoding="utf-8")
        )
        posts = [EvidencePost.model_validate(item) for item in payload]
        now = request.as_of or datetime(2026, 8, 19, tzinfo=UTC)
        start = now - timedelta(days=request.days)
        selected = [post for post in posts if start <= post.created_at <= now]
        coverage = Coverage(
            status=CoverageStatus.FULL,
            requested_from=start,
            requested_to=now,
            actual_from=min((post.created_at for post in selected), default=None),
            actual_to=max((post.created_at for post in selected), default=None),
            providers=[self.name],
            pages_fetched=1,
            candidate_cap=len(posts),
            complete=True,
        )
        return ProviderResponse(posts=selected, coverage=coverage, warnings=[])
