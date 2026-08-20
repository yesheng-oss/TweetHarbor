from __future__ import annotations

from datetime import datetime
from enum import StrEnum
from typing import Literal
from uuid import uuid4

from pydantic import BaseModel, Field, HttpUrl, field_validator


class CoverageStatus(StrEnum):
    FULL = "full"
    PARTIAL = "partial"
    UNSUPPORTED = "unsupported"


class PublicationBasis(StrEnum):
    PUBLISHER = "publisher"
    ROOT_POST = "root_post"
    FIRST_SEEN = "first_seen"


class AccessStatus(StrEnum):
    FULL = "full"
    METADATA_ONLY = "metadata_only"
    UNREADABLE = "unreadable"


class Engagement(BaseModel):
    likes: int = Field(default=0, ge=0)
    reposts: int = Field(default=0, ge=0)
    quotes: int = Field(default=0, ge=0)
    replies: int = Field(default=0, ge=0)

    @property
    def weighted(self) -> int:
        return self.likes + self.reposts * 3 + self.quotes * 4 + self.replies


class EvidencePost(BaseModel):
    post_id: str
    provider: str
    author_handle: str
    author_verified: bool = False
    created_at: datetime
    urls: list[str] = Field(default_factory=list)
    metrics: Engagement = Field(default_factory=Engagement)
    text: str = ""
    link_title: str | None = None
    link_summary: str | None = None
    link_published_at: datetime | None = None


class ScoreBreakdown(BaseModel):
    hotness: float = Field(ge=0, le=100)
    relevance: float = Field(ge=0, le=100)
    freshness: float = Field(ge=0, le=100)
    evidence: float = Field(ge=0, le=100)
    final: float = Field(ge=0, le=100)
    version: str = "article-v1"


class ArticleCandidate(BaseModel):
    article_id: str
    canonical_url: HttpUrl
    canonical_aliases: list[str] = Field(default_factory=list)
    title: str
    summary: str | None = None
    source_domain: str
    published_at: datetime | None = None
    publication_basis: PublicationBasis
    access_status: AccessStatus = AccessStatus.METADATA_ONLY
    eligibility: Literal["main", "uncertain_date"] = "main"
    evidence_posts: list[EvidencePost] = Field(default_factory=list)
    engagement: Engagement = Field(default_factory=Engagement)
    score: ScoreBreakdown | None = None
    rank: int | None = None


class Coverage(BaseModel):
    status: CoverageStatus
    requested_from: datetime
    requested_to: datetime
    actual_from: datetime | None = None
    actual_to: datetime | None = None
    providers: list[str] = Field(default_factory=list)
    pages_fetched: int = Field(default=0, ge=0)
    candidate_cap: int | None = Field(default=None, ge=1)
    complete: bool = False
    degraded_reasons: list[str] = Field(default_factory=list)


class DiscoverRequest(BaseModel):
    topic: str = Field(min_length=1, max_length=200)
    days: int = Field(default=7, ge=1, le=10)
    limit: int = Field(default=10, ge=1, le=50)
    provider: str = "fixture"
    languages: list[str] = Field(default_factory=lambda: ["en", "zh"])
    include_uncertain_dates: bool = False
    require_complete: bool = False
    as_of: datetime | None = None

    @field_validator("topic")
    @classmethod
    def normalize_topic(cls, value: str) -> str:
        normalized = " ".join(value.split())
        if not normalized:
            raise ValueError("topic cannot be blank")
        return normalized


class DiscoveryResult(BaseModel):
    schema_version: str = "1.0"
    run_id: str = Field(default_factory=lambda: str(uuid4()))
    status: Literal["ok", "partial"] = "ok"
    capability: str = "x_articles"
    request: DiscoverRequest
    coverage: Coverage
    items: list[ArticleCandidate] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    fetched_at: datetime


class DoctorReport(BaseModel):
    schema_version: str = "1.0"
    service: str = "tweetharbor"
    x_api_configured: bool
    agent_reach: dict[str, object] | None = None
    database_path: str
    supported_providers: list[str]
    warnings: list[str] = Field(default_factory=list)
