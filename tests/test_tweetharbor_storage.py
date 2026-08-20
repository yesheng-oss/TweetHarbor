from datetime import UTC, datetime

from tweetharbor.application.service import DiscoveryService
from tweetharbor.domain.models import DiscoverRequest
from tweetharbor.providers.fixture import FixtureProvider
from tweetharbor.storage.database import Database


def test_saved_run_round_trips_with_evidence(tmp_path) -> None:
    database = Database(tmp_path / "harbor.db")
    service = DiscoveryService({"fixture": FixtureProvider()}, database)
    result = service.discover(
        DiscoverRequest(
            topic="AI Agent",
            days=10,
            provider="fixture",
            as_of=datetime(2026, 8, 19, tzinfo=UTC),
        ),
        save=True,
    )

    loaded = database.get_run(result.run_id)
    assert loaded is not None
    assert loaded.run_id == result.run_id
    assert loaded.items[0].evidence_posts
    assert database.list_runs()[0]["run_id"] == result.run_id
