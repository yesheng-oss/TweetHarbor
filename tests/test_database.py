from datetime import date, datetime, timezone

from starscout.storage.database import Database
from starscout.storage.models import Repository


def repo(stars: int, forks: int = 10) -> Repository:
    return Repository(
        full_name="acme/demo",
        name="demo",
        owner="acme",
        description="Demo",
        stars=stars,
        forks=forks,
        open_issues=2,
        language="Python",
        created_at=datetime(2026, 7, 1, tzinfo=timezone.utc),
        updated_at=datetime(2026, 8, 18, tzinfo=timezone.utc),
        topics=["ai"],
        html_url="https://github.com/acme/demo",
    )


def test_snapshot_growth(tmp_path) -> None:
    db = Database(tmp_path / "starscout.db")
    db.save_snapshot(repo(100, 10), snapshot_date=date(2026, 8, 11))
    db.save_snapshot(repo(130, 14), snapshot_date=date(2026, 8, 15))
    current = repo(180, 20)
    db.save_snapshot(current, snapshot_date=date(2026, 8, 18))

    growth = db.growth_for(current, today=date(2026, 8, 18))
    assert growth.three_day_stars == 50
    assert growth.seven_day_stars == 80
    assert growth.fork_growth == 10
    assert growth.growth_rate == 0.8
