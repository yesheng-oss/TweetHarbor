from __future__ import annotations

import json
import sqlite3
from datetime import date, timedelta
from pathlib import Path

from starscout.storage.models import GrowthMetrics, Repository, Snapshot


DEFAULT_DB_PATH = Path(".starscout/starscout.db")


class Database:
    def __init__(self, path: str | Path = DEFAULT_DB_PATH) -> None:
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._init_schema()

    def connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.path)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_schema(self) -> None:
        with self.connect() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS repositories (
                    full_name TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    owner TEXT NOT NULL,
                    description TEXT,
                    language TEXT,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    topics TEXT NOT NULL,
                    html_url TEXT NOT NULL
                )
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS snapshots (
                    repo_name TEXT NOT NULL,
                    snapshot_date TEXT NOT NULL,
                    stars INTEGER NOT NULL,
                    forks INTEGER NOT NULL,
                    open_issues INTEGER NOT NULL,
                    PRIMARY KEY (repo_name, snapshot_date)
                )
                """
            )

    def upsert_repository(self, repo: Repository) -> None:
        with self.connect() as conn:
            conn.execute(
                """
                INSERT INTO repositories (
                    full_name, name, owner, description, language,
                    created_at, updated_at, topics, html_url
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(full_name) DO UPDATE SET
                    name=excluded.name,
                    owner=excluded.owner,
                    description=excluded.description,
                    language=excluded.language,
                    created_at=excluded.created_at,
                    updated_at=excluded.updated_at,
                    topics=excluded.topics,
                    html_url=excluded.html_url
                """,
                (
                    repo.full_name,
                    repo.name,
                    repo.owner,
                    repo.description,
                    repo.language,
                    repo.created_at.isoformat(),
                    repo.updated_at.isoformat(),
                    json.dumps(repo.topics),
                    str(repo.html_url),
                ),
            )

    def save_snapshot(self, repo: Repository, snapshot_date: date | None = None) -> None:
        day = snapshot_date or date.today()
        self.upsert_repository(repo)
        with self.connect() as conn:
            conn.execute(
                """
                INSERT INTO snapshots (repo_name, snapshot_date, stars, forks, open_issues)
                VALUES (?, ?, ?, ?, ?)
                ON CONFLICT(repo_name, snapshot_date) DO UPDATE SET
                    stars=excluded.stars,
                    forks=excluded.forks,
                    open_issues=excluded.open_issues
                """,
                (
                    repo.full_name,
                    day.isoformat(),
                    repo.stars,
                    repo.forks,
                    repo.open_issues,
                ),
            )

    def save_repositories(self, repos: list[Repository], snapshot_date: date | None = None) -> None:
        for repo in repos:
            self.save_snapshot(repo, snapshot_date=snapshot_date)

    def latest_snapshot(self, repo_name: str) -> Snapshot | None:
        with self.connect() as conn:
            row = conn.execute(
                """
                SELECT repo_name, snapshot_date, stars, forks, open_issues
                FROM snapshots
                WHERE repo_name = ?
                ORDER BY snapshot_date DESC
                LIMIT 1
                """,
                (repo_name,),
            ).fetchone()
        return self._snapshot_from_row(row) if row else None

    def snapshot_on_or_before(self, repo_name: str, target_date: date) -> Snapshot | None:
        with self.connect() as conn:
            row = conn.execute(
                """
                SELECT repo_name, snapshot_date, stars, forks, open_issues
                FROM snapshots
                WHERE repo_name = ? AND snapshot_date <= ?
                ORDER BY snapshot_date DESC
                LIMIT 1
                """,
                (repo_name, target_date.isoformat()),
            ).fetchone()
        return self._snapshot_from_row(row) if row else None

    def growth_for(self, repo: Repository, today: date | None = None) -> GrowthMetrics:
        day = today or date.today()
        one = self._star_delta(repo, day, 1)
        three = self._star_delta(repo, day, 3)
        seven = self._star_delta(repo, day, 7)
        fork_growth = self._fork_delta(repo, day, 7)
        base = self.snapshot_on_or_before(repo.full_name, day - timedelta(days=7))
        growth_rate = None
        if base and base.stars > 0 and seven is not None:
            growth_rate = seven / base.stars
        return GrowthMetrics(
            one_day_stars=one,
            three_day_stars=three,
            seven_day_stars=seven,
            fork_growth=fork_growth,
            growth_rate=growth_rate,
        )

    def _star_delta(self, repo: Repository, today: date, days: int) -> int | None:
        base = self.snapshot_on_or_before(repo.full_name, today - timedelta(days=days))
        if not base:
            return None
        return repo.stars - base.stars

    def _fork_delta(self, repo: Repository, today: date, days: int) -> int | None:
        base = self.snapshot_on_or_before(repo.full_name, today - timedelta(days=days))
        if not base:
            return None
        return repo.forks - base.forks

    @staticmethod
    def _snapshot_from_row(row: sqlite3.Row) -> Snapshot:
        return Snapshot(
            repo_name=row["repo_name"],
            stars=row["stars"],
            forks=row["forks"],
            open_issues=row["open_issues"],
            snapshot_date=date.fromisoformat(row["snapshot_date"]),
        )
