from __future__ import annotations

import os
from datetime import UTC, datetime, timedelta

import httpx

from tweetharbor.domain.errors import TweetHarborError
from tweetharbor.domain.models import (
    Coverage,
    CoverageStatus,
    DiscoverRequest,
    Engagement,
    EvidencePost,
)
from tweetharbor.providers.base import ProviderResponse


class XApiProvider:
    """Official X API search adapter with explicit coverage semantics."""

    name = "x-api"

    def __init__(self, bearer_token: str | None = None, timeout: float = 25.0) -> None:
        self.bearer_token = bearer_token or os.getenv("X_BEARER_TOKEN")
        self.timeout = timeout
        self.max_pages = max(1, int(os.getenv("TWEETHARBOR_X_MAX_PAGES", "5")))

    def discover(self, request: DiscoverRequest) -> ProviderResponse:
        if not self.bearer_token:
            raise TweetHarborError(
                "AUTH_MISSING",
                "X_BEARER_TOKEN is required for the official X API provider.",
                "Set X_BEARER_TOKEN or use --provider fixture for an offline demo.",
            )
        if request.days > 7 and os.getenv("TWEETHARBOR_X_FULL_ARCHIVE", "0") != "1":
            raise TweetHarborError(
                "TIME_WINDOW_UNSUPPORTED",
                "The official X Recent Search provider covers at most 7 days.",
                "Enable Full-Archive access and set TWEETHARBOR_X_FULL_ARCHIVE=1, or request 7 days.",
            )

        now = request.as_of or datetime.now(UTC)
        start = now - timedelta(days=request.days)
        endpoint = "/2/tweets/search/all" if request.days > 7 else "/2/tweets/search/recent"
        query = f"({request.topic}) has:links -is:retweet"
        params: dict[str, str | int] = {
            "query": query,
            "start_time": start.isoformat().replace("+00:00", "Z"),
            "end_time": now.isoformat().replace("+00:00", "Z"),
            "max_results": 100,
            "tweet.fields": "created_at,public_metrics,entities,author_id,lang",
            "expansions": "author_id",
            "user.fields": "username,verified",
        }
        headers = {"Authorization": f"Bearer {self.bearer_token}"}
        posts: list[EvidencePost] = []
        warnings: list[str] = []
        pages = 0
        next_token: str | None = None
        users: dict[str, dict[str, object]] = {}

        try:
            with httpx.Client(base_url="https://api.x.com", headers=headers, timeout=self.timeout) as client:
                while pages < self.max_pages:
                    if next_token:
                        params["next_token"] = next_token
                    response = client.get(endpoint, params=params)
                    if response.status_code in {429, 503}:
                        raise TweetHarborError(
                            "UPSTREAM_RATE_LIMITED",
                            f"X API returned HTTP {response.status_code}.",
                            "Retry later; do not switch to a non-API backend automatically.",
                            retryable=True,
                        )
                    if response.status_code >= 400:
                        raise TweetHarborError(
                            "UPSTREAM_REQUEST_FAILED",
                            f"X API returned HTTP {response.status_code}.",
                            "Check the token, X API product access, and query syntax.",
                        )
                    payload = response.json()
                    for user in payload.get("includes", {}).get("users", []):
                        users[str(user.get("id"))] = user
                    posts.extend(self._map_post(item, users) for item in payload.get("data", []))
                    pages += 1
                    next_token = payload.get("meta", {}).get("next_token")
                    if not next_token:
                        break
        except httpx.HTTPError as exc:
            raise TweetHarborError(
                "UPSTREAM_NETWORK_ERROR",
                "The X API request could not be completed.",
                "Check network access and retry later.",
                retryable=True,
            ) from exc

        complete = next_token is None
        if not complete:
            warnings.append(f"Stopped after configured page cap ({self.max_pages}).")
        coverage = Coverage(
            status=CoverageStatus.FULL if complete else CoverageStatus.PARTIAL,
            requested_from=start,
            requested_to=now,
            actual_from=min((post.created_at for post in posts), default=None),
            actual_to=max((post.created_at for post in posts), default=None),
            providers=[self.name],
            pages_fetched=pages,
            candidate_cap=self.max_pages * 100,
            complete=complete,
            degraded_reasons=[] if complete else ["page_cap_reached"],
        )
        return ProviderResponse(posts=posts, coverage=coverage, warnings=warnings)

    @staticmethod
    def _map_post(payload: dict[str, object], users: dict[str, dict[str, object]]) -> EvidencePost:
        entities = payload.get("entities") or {}
        urls = [
            str(item.get("expanded_url"))
            for item in entities.get("urls", [])
            if item.get("expanded_url")
        ]
        metrics = payload.get("public_metrics") or {}
        author = users.get(str(payload.get("author_id")), {})
        created_at = datetime.fromisoformat(str(payload["created_at"]).replace("Z", "+00:00"))
        text = str(payload.get("text", ""))
        return EvidencePost(
            post_id=str(payload["id"]),
            provider="x-api",
            author_handle=str(author.get("username", "unknown")),
            author_verified=bool(author.get("verified", False)),
            created_at=created_at,
            urls=urls,
            metrics=Engagement(
                likes=int(metrics.get("like_count", 0)),
                reposts=int(metrics.get("retweet_count", 0)),
                quotes=int(metrics.get("quote_count", 0)),
                replies=int(metrics.get("reply_count", 0)),
            ),
            text=text,
            link_title=text[:140] or None,
            # X supplies the evidence-post time. It is not publisher metadata, so the
            # record remains explicitly labeled as ROOT_POST and metadata-only.
            link_published_at=created_at,
        )
