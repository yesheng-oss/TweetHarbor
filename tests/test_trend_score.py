from datetime import datetime, timezone

from starscout.ranking.trend_score import TrendScore
from starscout.storage.models import GrowthMetrics, Repository


def make_repo(stars: int = 1000) -> Repository:
    return Repository(
        full_name="owner/repo",
        name="repo",
        owner="owner",
        description="Demo",
        stars=stars,
        forks=50,
        open_issues=4,
        language="Python",
        created_at=datetime(2026, 8, 1, tzinfo=timezone.utc),
        updated_at=datetime(2026, 8, 18, tzinfo=timezone.utc),
        topics=["ai"],
        html_url="https://github.com/owner/repo",
    )


def test_trend_score_range() -> None:
    score = TrendScore().calculate(
        make_repo(),
        GrowthMetrics(seven_day_stars=100, fork_growth=10, growth_rate=0.1),
        now=datetime(2026, 8, 18, tzinfo=timezone.utc),
    )
    assert 0 <= score <= 100


def test_growth_increases_score() -> None:
    scorer = TrendScore()
    repo = make_repo()
    low = scorer.calculate(repo, GrowthMetrics(seven_day_stars=0), now=datetime(2026, 8, 18, tzinfo=timezone.utc))
    high = scorer.calculate(repo, GrowthMetrics(seven_day_stars=400), now=datetime(2026, 8, 18, tzinfo=timezone.utc))
    assert high > low
