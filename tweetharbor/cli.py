from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Annotated

import typer
from dotenv import load_dotenv

from tweetharbor.application.service import DiscoveryService
from tweetharbor.diagnostics import build_doctor_report
from tweetharbor.domain.errors import TweetHarborError
from tweetharbor.domain.models import DiscoverRequest
from tweetharbor.output.renderers import render_json, render_markdown
from tweetharbor.providers.fixture import FixtureProvider
from tweetharbor.providers.x_api import XApiProvider
from tweetharbor.storage.database import DEFAULT_DB_PATH, Database

app = typer.Typer(
    help="Evidence-first discovery of important X articles for Codex.",
    no_args_is_help=True,
    add_completion=False,
)


def _database_path(value: Path | None) -> Path:
    configured = os.getenv("TWEETHARBOR_DB_PATH")
    return value or Path(configured) if configured else value or DEFAULT_DB_PATH


def _service(db_path: Path | None) -> DiscoveryService:
    load_dotenv()
    database = Database(_database_path(db_path))
    return DiscoveryService({"fixture": FixtureProvider(), "x-api": XApiProvider()}, database)


@app.callback()
def main(
    ctx: typer.Context,
    db_path: Annotated[Path | None, typer.Option("--db-path", help="SQLite database path.")] = None,
) -> None:
    """Configure TweetHarbor without causing network or database writes."""
    ctx.obj = {"db_path": db_path}


def _emit_error(error: TweetHarborError, output_format: str) -> None:
    if output_format == "json":
        typer.echo(json.dumps({"status": "error", "error": error.as_dict()}, indent=2))
    else:
        typer.echo(f"Error [{error.code}]: {error.message}", err=True)
        if error.remediation:
            typer.echo(f"Next step: {error.remediation}", err=True)


def _write_result(result: object, output_format: str) -> None:
    if output_format == "json":
        typer.echo(render_json(result))
    else:
        typer.echo(render_markdown(result))


@app.command()
def doctor(
    ctx: typer.Context,
    output_format: Annotated[str, typer.Option("--format", help="json or md")] = "json",
) -> None:
    """Show safe provider, credential, database, and Agent Reach diagnostics."""
    if output_format not in {"json", "md"}:
        raise typer.BadParameter("format must be json or md")
    report = build_doctor_report(_database_path(ctx.obj.get("db_path")))
    if output_format == "json":
        typer.echo(report.model_dump_json(indent=2))
    else:
        typer.echo("# TweetHarbor doctor\n")
        typer.echo(f"- X API configured: `{report.x_api_configured}`")
        typer.echo(f"- Database: `{report.database_path}`")
        typer.echo(f"- Providers: {', '.join(report.supported_providers)}")
        for warning in report.warnings:
            typer.echo(f"- Warning: {warning}")


@app.command()
def discover(
    ctx: typer.Context,
    topic: Annotated[str, typer.Argument(help="Topic or X query concept, e.g. 'AI Agent'.")],
    days: Annotated[int, typer.Option("--days", min=1, max=10)] = 7,
    top: Annotated[int, typer.Option("--top", min=1, max=50)] = 10,
    provider: Annotated[str, typer.Option("--provider", help="fixture or x-api")] = "fixture",
    output_format: Annotated[str, typer.Option("--format", help="json or md")] = "md",
    include_uncertain_dates: Annotated[bool, typer.Option("--include-uncertain-dates")] = False,
    save: Annotated[bool, typer.Option("--save", help="Persist this run and evidence to SQLite.")] = False,
) -> None:
    """Find and rank external articles. Reads by default; --save is explicit."""
    if output_format not in {"json", "md"}:
        raise typer.BadParameter("format must be json or md")
    request = DiscoverRequest(
        topic=topic,
        days=days,
        limit=top,
        provider=provider,
        include_uncertain_dates=include_uncertain_dates,
    )
    try:
        result = _service(ctx.obj.get("db_path")).discover(request, save=save)
    except TweetHarborError as error:
        _emit_error(error, output_format)
        raise typer.Exit(code=2) from error
    _write_result(result, output_format)


@app.command()
def snapshot(
    ctx: typer.Context,
    topic: Annotated[str, typer.Argument(help="Topic or X query concept.")],
    days: Annotated[int, typer.Option("--days", min=1, max=10)] = 7,
    provider: Annotated[str, typer.Option("--provider")] = "fixture",
    output_format: Annotated[str, typer.Option("--format")] = "json",
) -> None:
    """Explicitly persist one discovery run for later review."""
    request = DiscoverRequest(topic=topic, days=days, provider=provider)
    try:
        result = _service(ctx.obj.get("db_path")).discover(request, save=True)
    except TweetHarborError as error:
        _emit_error(error, output_format)
        raise typer.Exit(code=2) from error
    _write_result(result, output_format)


@app.command("get-run")
def get_run(
    ctx: typer.Context,
    run_id: Annotated[str, typer.Argument(help="Persisted discovery run identifier.")],
    output_format: Annotated[str, typer.Option("--format")] = "json",
) -> None:
    """Load an explicit saved run without calling any provider."""
    result = _service(ctx.obj.get("db_path")).database.get_run(run_id)
    if result is None:
        error = TweetHarborError("RUN_NOT_FOUND", f"No saved run named '{run_id}'.")
        _emit_error(error, output_format)
        raise typer.Exit(code=2)
    _write_result(result, output_format)


@app.command()
def runs(
    ctx: typer.Context,
    limit: Annotated[int, typer.Option("--limit", min=1, max=100)] = 20,
) -> None:
    """List persisted discovery runs as JSON."""
    payload = _service(ctx.obj.get("db_path")).database.list_runs(limit=limit)
    typer.echo(json.dumps(payload, indent=2))


@app.command("mcp-serve")
def mcp_serve(ctx: typer.Context) -> None:
    """Start the optional local STDIO MCP server."""
    from tweetharbor.mcp_server import run_stdio

    run_stdio(_database_path(ctx.obj.get("db_path")))


if __name__ == "__main__":
    app()
