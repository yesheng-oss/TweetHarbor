from __future__ import annotations

import math
from datetime import datetime, timezone

from starscout.ranking.velocity import normalize
from starscout.storage.models import GrowthMetrics, Repository


class TrendScore:
    """GitHub-only trend score.

    Score components are intentionally independent so future collectors can add
    social/news signals without rewriting the GitHub scoring logic.
    """

    def calculate(self, repo: Repository, growth: GrowthMetrics, now: datetime | None = None) -> float:
        current = now or datetime.now(timezone.utc)
        star_velocity = normalize(float(growth.seven_day_stars or growth.three_day_stars or growth.one_day_stars or 0), 500)
        total_stars = normalize(math.log10(repo.stars + 1), 5)
        fork_velocity = normalize(float(growth.fork_growth or 0), 100)
        freshness = self._freshness(repo.created_at, current)
        activity = self._activity(repo.updated_at, current)

        score = (
            star_velocity * 45
            + total_stars * 20
            + fork_velocity * 15
            + freshness * 10
            + activity * 10
        )
        return round(max(0.0, min(score, 100.0)), 2)

    @staticmethod
    def _freshness(created_at: datetime, now: datetime) -> float:
        age_days = max((now - _aware(created_at)).days, 0)
        if age_days <= 30:
            return 1.0
        if age_days >= 365:
            return 0.1
        return 1.0 - ((age_days - 30) / 335) * 0.9

    @staticmethod
    def _activity(updated_at: datetime, now: datetime) -> float:
        idle_days = max((now - _aware(updated_at)).days, 0)
        if idle_days <= 3:
            return 1.0
        if idle_days >= 90:
            return 0.0
        return 1.0 - ((idle_days - 3) / 87)


def _aware(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)
