from __future__ import annotations

import hashlib
from collections import defaultdict
from datetime import datetime
from urllib.parse import urlsplit

from tweetharbor.domain.errors import TweetHarborError
from tweetharbor.domain.models import (
    AccessStatus,
    ArticleCandidate,
    DiscoverRequest,
    DiscoveryResult,
    Engagement,
    EvidencePost,
    PublicationBasis,
)
from tweetharbor.extractors.urls import canonicalize_url, is_external_article
from tweetharbor.providers.base import ArticleProvider
from tweetharbor.ranking.articles import rank_articles
from tweetharbor.storage.database import Database


class DiscoveryService:
    def __init__(self, providers: dict[str, ArticleProvider], database: Database) -> None:
        self.providers = providers
        self.database = database

    def discover(self, request: DiscoverRequest, *, save: bool = False) -> DiscoveryResult:
        provider = self.providers.get(request.provider)
        if provider is None:
            raise TweetHarborError(
                "PROVIDER_UNAVAILABLE",
                f"Provider '{request.provider}' is not registered.",
                f"Choose one of: {', '.join(sorted(self.providers))}.",
            )
        response = provider.discover(request)
        if request.require_complete and not response.coverage.complete:
            reasons = "; ".join(response.coverage.degraded_reasons) or "provider returned partial coverage"
            raise TweetHarborError(
                "COVERAGE_INCOMPLETE",
                "The provider cannot satisfy this request with complete coverage.",
                f"Relax require_complete or change provider/access level ({reasons}).",
            )
        # Providers define the observation clock. Fixtures deliberately use a
        # fixed clock so demos and golden tests remain reproducible.
        now = request.as_of or response.coverage.requested_to
        articles, warnings = self._assemble_articles(response.posts, request, now)
        ranked = rank_articles(articles, request.topic, now)[: request.limit]
        status = "partial" if not response.coverage.complete else "ok"
        result = DiscoveryResult(
            status=status,
            request=request,
            coverage=response.coverage,
            items=ranked,
            warnings=[*response.warnings, *warnings],
            fetched_at=now,
        )
        if save:
            self.database.save_result(result)
        return result

    @staticmethod
    def _assemble_articles(
        posts: list[EvidencePost], request: DiscoverRequest, now: datetime
    ) -> tuple[list[ArticleCandidate], list[str]]:
        grouped: dict[str, list[EvidencePost]] = defaultdict(list)
        aliases: dict[str, set[str]] = defaultdict(set)
        for post in posts:
            for url in post.urls:
                if not is_external_article(url):
                    continue
                canonical = canonicalize_url(url)
                if canonical:
                    grouped[canonical].append(post)
                    aliases[canonical].add(url)

        articles: list[ArticleCandidate] = []
        warnings: list[str] = []
        for canonical, evidence in grouped.items():
            representative = max(evidence, key=lambda item: item.metrics.weighted)
            publication_dates = [post.link_published_at for post in evidence if post.link_published_at]
            if publication_dates:
                published_at = min(publication_dates)
                basis = PublicationBasis.ROOT_POST if representative.provider == "x-api" else PublicationBasis.PUBLISHER
                eligibility = "main"
            else:
                published_at = min(post.created_at for post in evidence)
                basis = PublicationBasis.FIRST_SEEN
                eligibility = "uncertain_date"
            if eligibility == "uncertain_date" and not request.include_uncertain_dates:
                warnings.append(f"Excluded date-uncertain article: {canonical}")
                continue
            engagement = Engagement(
                likes=sum(post.metrics.likes for post in evidence),
                reposts=sum(post.metrics.reposts for post in evidence),
                quotes=sum(post.metrics.quotes for post in evidence),
                replies=sum(post.metrics.replies for post in evidence),
            )
            article_id = hashlib.sha256(canonical.encode("utf-8")).hexdigest()[:16]
            articles.append(
                ArticleCandidate(
                    article_id=article_id,
                    canonical_url=canonical,
                    canonical_aliases=sorted(aliases[canonical]),
                    title=representative.link_title or canonical,
                    summary=representative.link_summary,
                    source_domain=urlsplit(canonical).netloc,
                    published_at=published_at,
                    publication_basis=basis,
                    access_status=AccessStatus.METADATA_ONLY,
                    eligibility=eligibility,
                    evidence_posts=evidence,
                    engagement=engagement,
                )
            )
        return articles, warnings
