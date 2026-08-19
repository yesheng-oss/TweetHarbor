# StarScout

Find tomorrow's trending GitHub repositories today.

StarScout is a CLI MVP for discovering fast-growing GitHub repositories in a specific domain, such as `AI Agent`, `MCP`, `RAG`, `AI Video`, or `Coding Agent`.

## Features

- Search GitHub repositories by topic or keyword.
- Store daily repository snapshots in SQLite.
- Calculate 1-day, 3-day, and 7-day star growth when historical data exists.
- Rank repositories with a modular 0-100 Trend Score.
- Render useful terminal tables with Rich.

## Install

```bash
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -e ".[dev]"
```

Optional but recommended:

```bash
copy .env.example .env
```

Set `GITHUB_TOKEN` in `.env` to increase GitHub API rate limits.

## Usage

Search repositories and save today's snapshots:

```bash
starscout search "AI Agent"
```

Show trending repositories by 7-day growth and Trend Score:

```bash
starscout trending "AI Agent"
```

Use a custom database:

```bash
starscout --db-path .starscout/demo.db search "RAG"
```

## MVP Scope

This first version only uses GitHub data. The scoring engine is intentionally modular so future versions can add signals from X, Reddit, YouTube, Hacker News, package managers, and developer communities.

## Development

```bash
pytest
```
