from __future__ import annotations

import os
from datetime import date
from pathlib import Path

import typer
from dotenv import load_dotenv

from starscout.collectors.github import GitHubCollector
from starscout.output.console import console, render_search_results, render_trending
from starscout.ranking.trend_score import TrendScore
from starscout.storage.database import DEFAULT_DB_PATH, Database
from starscout.storage.models import RankedRepository, Repository

app = typer.Typer(help="Find tomorrow's trending GitHub repositories today.")


def _rank(repos: list[Repository], db: Database) -> list[RankedRepository]:
    scorer = TrendScore()
    rows: list[RankedRepository] = []
    for repo in repos:
        growth = db.growth_for(repo)
        rows.append(
            RankedRepository(
                repository=repo,
                growth=growth,
                trend_score=scorer.calculate(repo, growth),
            )
        )
    return rows


def _database(db_path: Path | None) -> Database:
    load_dotenv()
    configured = os.getenv("STARSCOUT_DB_PATH")
    return Database(db_path or configured or DEFAULT_DB_PATH)


@app.callback()
def main(
    ctx: typer.Context,
    db_path: Path | None = typer.Option(None, "--db-path", help="SQLite database path."),
) -> None:
    ctx.obj = {"db_path": db_path}


@app.command()
def search(
    ctx: typer.Context,
    query: str = typer.Argument(..., help="Domain or keyword, e.g. 'AI Agent'."),
    limit: int = typer.Option(20, "--limit", "-n", min=1, max=100, help="Number of repositories to fetch."),
) -> None:
    """Search GitHub repositories and save today's snapshot."""
    db = _database(ctx.obj.get("db_path"))
    collector = GitHubCollector()
    try:
        repos = collector.search_repositories(query, limit=limit)
    except Exception as exc:
        console.print(f"[red]GitHub search failed:[/red] {exc}")
        raise typer.Exit(code=1) from exc

    db.save_repositories(repos, snapshot_date=date.today())
    ranked = _rank(repos, db)
    render_search_results(ranked)


@app.command()
def trending(
    ctx: typer.Context,
    query: str = typer.Argument(..., help="Domain or keyword, e.g. 'AI Agent'."),
    limit: int = typer.Option(20, "--limit", "-n", min=1, max=100, help="Number of repositories to fetch."),
) -> None:
    """Show repositories ranked by recent growth and Trend Score."""
    db = _database(ctx.obj.get("db_path"))
    collector = GitHubCollector()
    try:
        repos = collector.search_repositories(query, limit=limit)
    except Exception as exc:
        console.print(f"[red]GitHub search failed:[/red] {exc}")
        raise typer.Exit(code=1) from exc

    db.save_repositories(repos, snapshot_date=date.today())
    ranked = _rank(repos, db)
    ranked.sort(
        key=lambda row: (
            row.growth.seven_day_stars if row.growth.seven_day_stars is not None else -1,
            row.trend_score,
            row.repository.stars,
        ),
        reverse=True,
    )
    render_trending(ranked[:limit])


if __name__ == "__main__":
    app()
