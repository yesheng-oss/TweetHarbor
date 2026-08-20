from __future__ import annotations

from pathlib import Path
from typing import Any

from tweetharbor.application.service import DiscoveryService
from tweetharbor.diagnostics import build_doctor_report
from tweetharbor.domain.errors import TweetHarborError
from tweetharbor.domain.models import DiscoverRequest
from tweetharbor.providers.fixture import FixtureProvider
from tweetharbor.providers.x_api import XApiProvider
from tweetharbor.storage.database import DEFAULT_DB_PATH, Database

SERVER_INSTRUCTIONS = (
    "TweetHarbor discovers external articles shared on X. Read tools are side-effect free; "
    "save_snapshot writes only when explicitly called. Always report coverage and never claim a "
    "10-day result is complete without Full-Archive coverage. The fixture provider is an offline demo."
)


def _service(path: Path) -> DiscoveryService:
    return DiscoveryService({"fixture": FixtureProvider(), "x-api": XApiProvider()}, Database(path))


def create_server(db_path: Path = DEFAULT_DB_PATH) -> Any:
    """Create a real MCP server when the optional `mcp` dependency is installed."""
    try:
        from mcp.server.mcpserver import MCPServer
    except ImportError as exc:  # pragma: no cover - exercised by manual setup
        raise RuntimeError("Install TweetHarbor with `pip install -e \".[mcp]\"` to enable MCP.") from exc

    server = MCPServer("TweetHarbor", instructions=SERVER_INSTRUCTIONS)

    @server.tool()
    def doctor() -> dict[str, object]:
        """Report local provider and credential readiness without reading posts."""
        return build_doctor_report(db_path).model_dump(mode="json")

    @server.tool()
    def discover_articles(
        topic: str,
        days: int = 7,
        limit: int = 10,
        provider: str = "fixture",
        include_uncertain_dates: bool = False,
    ) -> dict[str, object]:
        """Discover important external articles with structured coverage and evidence."""
        try:
            result = _service(db_path).discover(
                DiscoverRequest(
                    topic=topic,
                    days=days,
                    limit=limit,
                    provider=provider,
                    include_uncertain_dates=include_uncertain_dates,
                ),
                save=False,
            )
            return result.model_dump(mode="json")
        except TweetHarborError as error:
            return {"status": "error", "error": error.as_dict()}

    @server.tool()
    def get_run(run_id: str) -> dict[str, object]:
        """Load one previously saved discovery run."""
        result = _service(db_path).database.get_run(run_id)
        if result is None:
            return {"status": "error", "error": {"code": "RUN_NOT_FOUND", "message": "Run not found."}}
        return result.model_dump(mode="json")

    @server.tool()
    def save_snapshot(topic: str, days: int = 7, provider: str = "fixture") -> dict[str, object]:
        """Explicitly save a discovery snapshot. This is the only writing MCP tool."""
        try:
            result = _service(db_path).discover(
                DiscoverRequest(topic=topic, days=days, provider=provider), save=True
            )
            return result.model_dump(mode="json")
        except TweetHarborError as error:
            return {"status": "error", "error": error.as_dict()}

    return server


def run_stdio(db_path: Path = DEFAULT_DB_PATH) -> None:
    create_server(db_path).run(transport="stdio")
