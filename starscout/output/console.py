from __future__ import annotations

from rich import box
from rich.console import Console
from rich.table import Table

from starscout.storage.models import RankedRepository, Repository


console = Console(width=160, color_system=None)


def _display(value: object, max_len: int | None = None) -> str:
    text = "" if value is None else str(value)
    safe = text.encode("ascii", errors="ignore").decode("ascii")
    safe = " ".join(safe.split())
    if max_len is not None and len(safe) > max_len:
        return safe[: max_len - 3] + "..."
    return safe or "-"


def render_search_results(rows: list[RankedRepository]) -> None:
    table = Table(title="StarScout Search Results", box=box.ASCII, expand=True)
    table.add_column("Repository", style="cyan", no_wrap=True, min_width=24)
    table.add_column("Description", overflow="fold", max_width=42)
    table.add_column("Stars", justify="right", no_wrap=True, min_width=7)
    table.add_column("Forks", justify="right", no_wrap=True, min_width=6)
    table.add_column("Lang", no_wrap=True, min_width=8)
    table.add_column("Created", no_wrap=True, min_width=10)
    table.add_column("Updated", no_wrap=True, min_width=10)
    table.add_column("Topics", overflow="fold", max_width=28)
    table.add_column("URL", style="blue", overflow="fold", max_width=38)

    for row in rows:
        repo = row.repository
        table.add_row(
            _display(repo.full_name),
            _display(repo.description, 140),
            str(repo.stars),
            str(repo.forks),
            _display(repo.language),
            repo.created_at.date().isoformat(),
            repo.updated_at.date().isoformat(),
            _display(", ".join(repo.topics[:4])),
            _display(repo.html_url),
        )
    console.print(table)


def render_trending(rows: list[RankedRepository]) -> None:
    table = Table(title="StarScout Trending", box=box.ASCII, expand=True)
    table.add_column("Rank", justify="right")
    table.add_column("Repository", style="cyan", no_wrap=True, min_width=28)
    table.add_column("Stars", justify="right")
    table.add_column("7d Growth", justify="right")
    table.add_column("Growth Rate", justify="right")
    table.add_column("Trend Score", justify="right", style="green")

    for index, row in enumerate(rows, start=1):
        growth = row.growth
        rate = "-" if growth.growth_rate is None else f"{growth.growth_rate:.1%}"
        seven = "-" if growth.seven_day_stars is None else str(growth.seven_day_stars)
        table.add_row(
            str(index),
            _display(row.repository.full_name),
            str(row.repository.stars),
            seven,
            rate,
            f"{row.trend_score:.2f}",
        )
    console.print(table)


def render_repo_detail(repo: Repository) -> None:
    console.print(f"[bold cyan]{repo.full_name}[/bold cyan]")
    console.print(repo.description or "No description")
    console.print(str(repo.html_url))
