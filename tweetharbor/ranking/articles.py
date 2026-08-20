from __future__ import annotations

import math
import re
from datetime import UTC, datetime

from tweetharbor.domain.models import ArticleCandidate, ScoreBreakdown

SCORE_VERSION = "article-v1"


def rank_articles(
    articles: list[ArticleCandidate], topic: str, now: datetime
) -> list[ArticleCandidate]:
    """Rank by evidence-backed heat, relevance, freshness, and independent shares."""
    max_weight = max((article.engagement.weighted for article in articles), default=1)
    terms = set(re.findall(r"[\w-]+", topic.lower()))
    for article in articles:
        haystack = " ".join(filter(None, [article.title, article.summary or ""])).lower()
        matches = sum(1 for term in terms if term in haystack)
        relevance = 100.0 * matches / max(len(terms), 1)
        hotness = 100.0 * math.log1p(article.engagement.weighted) / math.log1p(max_weight)
        reference_time = article.published_at or max(
            post.created_at for post in article.evidence_posts
        )
        age_hours = max((now - reference_time.astimezone(UTC)).total_seconds() / 3600, 0)
        freshness = max(0.0, 100.0 * (1 - age_hours / (14 * 24)))
        verified = sum(1 for post in article.evidence_posts if post.author_verified)
        evidence = min(100.0, len(article.evidence_posts) * 22 + verified * 12)
        final = round(hotness * 0.50 + relevance * 0.25 + freshness * 0.15 + evidence * 0.10, 2)
        article.score = ScoreBreakdown(
            hotness=round(hotness, 2),
            relevance=round(relevance, 2),
            freshness=round(freshness, 2),
            evidence=round(evidence, 2),
            final=final,
            version=SCORE_VERSION,
        )
    articles.sort(
        key=lambda item: (
            -(item.score.final if item.score else 0),
            -(item.published_at.timestamp() if item.published_at else 0),
            str(item.canonical_url),
        )
    )
    for index, article in enumerate(articles, start=1):
        article.rank = index
    return articles
