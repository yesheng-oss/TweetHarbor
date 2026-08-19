from __future__ import annotations

from datetime import date, datetime
from typing import Any

from pydantic import BaseModel, Field, HttpUrl


class Repository(BaseModel):
    full_name: str
    name: str
    owner: str
    description: str | None = None
    stars: int = 0
    forks: int = 0
    open_issues: int = 0
    language: str | None = None
    created_at: datetime
    updated_at: datetime
    topics: list[str] = Field(default_factory=list)
    html_url: HttpUrl

    @classmethod
    def from_github(cls, payload: dict[str, Any]) -> "Repository":
        owner = payload.get("owner") or {}
        return cls(
            full_name=payload["full_name"],
            name=payload["name"],
            owner=owner.get("login", ""),
            description=payload.get("description"),
            stars=payload.get("stargazers_count", 0),
            forks=payload.get("forks_count", 0),
            open_issues=payload.get("open_issues_count", 0),
            language=payload.get("language"),
            created_at=payload["created_at"],
            updated_at=payload["updated_at"],
            topics=payload.get("topics") or [],
            html_url=payload["html_url"],
        )


class Snapshot(BaseModel):
    repo_name: str
    stars: int
    forks: int
    open_issues: int
    snapshot_date: date


class GrowthMetrics(BaseModel):
    one_day_stars: int | None = None
    three_day_stars: int | None = None
    seven_day_stars: int | None = None
    fork_growth: int | None = None
    growth_rate: float | None = None


class RankedRepository(BaseModel):
    repository: Repository
    growth: GrowthMetrics
    trend_score: float
