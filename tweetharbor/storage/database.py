from __future__ import annotations

import json
import sqlite3
from pathlib import Path

from tweetharbor.domain.models import DiscoveryResult

DEFAULT_DB_PATH = Path(".tweetharbor/tweetharbor.db")


class Database:
    """Small SQLite repository with one transaction per saved discovery run."""

    def __init__(self, path: str | Path = DEFAULT_DB_PATH) -> None:
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._initialize()

    def connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.path)
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA foreign_keys = ON")
        connection.execute("PRAGMA journal_mode = WAL")
        return connection

    def _initialize(self) -> None:
        with self.connect() as conn:
            conn.executescript(
                """
                CREATE TABLE IF NOT EXISTS query_runs (
                    run_id TEXT PRIMARY KEY,
                    created_at TEXT NOT NULL,
                    status TEXT NOT NULL,
                    request_json TEXT NOT NULL,
                    coverage_json TEXT NOT NULL,
                    result_json TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS articles (
                    article_id TEXT PRIMARY KEY,
                    canonical_url TEXT NOT NULL UNIQUE,
                    title TEXT NOT NULL,
                    last_seen_at TEXT NOT NULL,
                    article_json TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS evidence_posts (
                    provider TEXT NOT NULL,
                    post_id TEXT NOT NULL,
                    article_id TEXT NOT NULL REFERENCES articles(article_id),
                    observed_at TEXT NOT NULL,
                    post_json TEXT NOT NULL,
                    PRIMARY KEY (provider, post_id)
                );
                CREATE TABLE IF NOT EXISTS run_articles (
                    run_id TEXT NOT NULL REFERENCES query_runs(run_id) ON DELETE CASCADE,
                    article_id TEXT NOT NULL REFERENCES articles(article_id),
                    rank INTEGER NOT NULL,
                    score REAL NOT NULL,
                    PRIMARY KEY (run_id, article_id)
                );
                CREATE INDEX IF NOT EXISTS idx_run_articles_rank ON run_articles(run_id, rank);
                """
            )

    def save_result(self, result: DiscoveryResult) -> None:
        result_json = result.model_dump(mode="json")
        with self.connect() as conn:
            conn.execute(
                """
                INSERT INTO query_runs(run_id, created_at, status, request_json, coverage_json, result_json)
                VALUES (?, ?, ?, ?, ?, ?)
                ON CONFLICT(run_id) DO UPDATE SET result_json=excluded.result_json
                """,
                (
                    result.run_id,
                    result.fetched_at.isoformat(),
                    result.status,
                    json.dumps(result_json["request"], sort_keys=True),
                    json.dumps(result_json["coverage"], sort_keys=True),
                    json.dumps(result_json, sort_keys=True),
                ),
            )
            for article in result.items:
                article_json = article.model_dump(mode="json")
                conn.execute(
                    """
                    INSERT INTO articles(article_id, canonical_url, title, last_seen_at, article_json)
                    VALUES (?, ?, ?, ?, ?)
                    ON CONFLICT(article_id) DO UPDATE SET
                        title=excluded.title,
                        last_seen_at=excluded.last_seen_at,
                        article_json=excluded.article_json
                    """,
                    (
                        article.article_id,
                        str(article.canonical_url),
                        article.title,
                        result.fetched_at.isoformat(),
                        json.dumps(article_json, sort_keys=True),
                    ),
                )
                for post in article.evidence_posts:
                    conn.execute(
                        """
                        INSERT INTO evidence_posts(provider, post_id, article_id, observed_at, post_json)
                        VALUES (?, ?, ?, ?, ?)
                        ON CONFLICT(provider, post_id) DO UPDATE SET
                            article_id=excluded.article_id,
                            observed_at=excluded.observed_at,
                            post_json=excluded.post_json
                        """,
                        (
                            post.provider,
                            post.post_id,
                            article.article_id,
                            result.fetched_at.isoformat(),
                            json.dumps(post.model_dump(mode="json"), sort_keys=True),
                        ),
                    )
                conn.execute(
                    """
                    INSERT INTO run_articles(run_id, article_id, rank, score)
                    VALUES (?, ?, ?, ?)
                    """,
                    (result.run_id, article.article_id, article.rank or 0, article.score.final if article.score else 0),
                )

    def get_run(self, run_id: str) -> DiscoveryResult | None:
        with self.connect() as conn:
            row = conn.execute("SELECT result_json FROM query_runs WHERE run_id = ?", (run_id,)).fetchone()
        return DiscoveryResult.model_validate_json(row["result_json"]) if row else None

    def list_runs(self, limit: int = 20) -> list[dict[str, object]]:
        with self.connect() as conn:
            rows = conn.execute(
                "SELECT run_id, created_at, status, request_json, coverage_json FROM query_runs ORDER BY created_at DESC LIMIT ?",
                (limit,),
            ).fetchall()
        return [
            {
                "run_id": row["run_id"],
                "created_at": row["created_at"],
                "status": row["status"],
                "request": json.loads(row["request_json"]),
                "coverage": json.loads(row["coverage_json"]),
            }
            for row in rows
        ]
