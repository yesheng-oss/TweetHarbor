from __future__ import annotations

import os

import httpx

from starscout.storage.models import Repository


class GitHubCollector:
    def __init__(self, token: str | None = None, timeout: float = 20.0) -> None:
        self.token = token or os.getenv("GITHUB_TOKEN")
        self.timeout = timeout

    def search_repositories(self, query: str, limit: int = 20) -> list[Repository]:
        per_page = max(1, min(limit, 100))
        headers = {
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
        }
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"

        params = {
            "q": self._build_query(query),
            "sort": "stars",
            "order": "desc",
            "per_page": per_page,
        }
        with httpx.Client(base_url="https://api.github.com", headers=headers, timeout=self.timeout) as client:
            response = client.get("/search/repositories", params=params)
            response.raise_for_status()
            payload = response.json()
        return [Repository.from_github(item) for item in payload.get("items", [])[:limit]]

    @staticmethod
    def _build_query(query: str) -> str:
        stripped = query.strip()
        if not stripped:
            raise ValueError("Query cannot be empty")
        # Keep MVP query broad but focused on real repos.
        return f"{stripped} in:name,description,topics stars:>=10"
