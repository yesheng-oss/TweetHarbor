# TweetHarbor

> Evidence-first discovery of important external articles shared on X, built for humans and Codex.

TweetHarbor turns a request such as “找近 7 天 X 上最重要的 AI Agent 文章” into a ranked article list with direct links, evidence-post counts, a versioned score, and an honest coverage statement.

It is deliberately **not** an automated posting, liking, or browser-cookie tool. Production X search uses the official X API. The included fixture provider makes every core workflow testable without a token or network access.

## What works today

- Discover and exactly deduplicate external article URLs.
- Rank candidates with a deterministic `article-v1` score: hotness, relevance, freshness, and independent evidence.
- Return the same result as JSON or Markdown.
- Persist only explicit snapshots in SQLite and reload them by run ID.
- Report unsupported 10-day requests truthfully when only Recent Search is available.
- Ship a repository-level Codex Skill at `.agents/skills/tweet-harbor`.
- Offer an optional local STDIO MCP server after installing the `mcp` extra.

## Quick start

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -e ".[dev]"

# Offline, deterministic demo. No credential or network required.
tweetharbor discover "AI Agent" --days 10 --provider fixture --format md

# Machine-readable output for Codex, scripts, and CI.
tweetharbor discover "AI Agent" --days 10 --provider fixture --format json --save
tweetharbor runs
```

## Live X API use

Copy `.env.example` to `.env`, then configure an official bearer token:

```text
X_BEARER_TOKEN=...
```

```powershell
tweetharbor doctor --format json
tweetharbor discover "AI Agent" --days 7 --provider x-api --format md
```

Recent Search covers at most 7 days. A 10-day live request needs Full-Archive access and explicit configuration:

```text
TWEETHARBOR_X_FULL_ARCHIVE=1
```

Without it, TweetHarbor returns `TIME_WINDOW_UNSUPPORTED`; it never presents seven days as a complete ten-day answer.

## Codex Skill

When Codex runs inside this repository, it discovers `.agents/skills/tweet-harbor` automatically. Invoke it directly with `$tweet-harbor`, or ask a matching question in natural language.

The Skill checks `tweetharbor doctor` first, prefers the official live provider when it is configured, and reports coverage/warnings instead of inventing certainty. See [Codex integration](docs/codex.md).

## Optional MCP

```powershell
pip install -e ".[mcp]"
codex mcp add tweetharbor -- tweetharbor mcp-serve
```

The STDIO server exposes `doctor`, `discover_articles`, `get_run`, and explicit `save_snapshot`. It uses the same application service as the CLI. See [the example configuration](docs/mcp-config.toml.example).

## Architecture and guarantees

- Providers return evidence and Coverage; they do not rank or render output.
- `discover` is read-only by default. `snapshot` and `discover --save` are explicit local writes.
- Date-uncertain articles are excluded by default and can be included only with `--include-uncertain-dates`.
- `null` means unknown. It never means zero.
- Agent Reach is used only for local capability diagnostics; it is not a silent fallback when the official X API fails.

Read [architecture](docs/architecture.md) and [provider policy](docs/provider-policy.md) before adding a provider.

## Legacy StarScout command

The repository originally shipped `starscout`, a GitHub repository trend prototype. It remains available during the 0.2 transition, but it is not used to answer X article requests and will not be mixed into TweetHarbor rankings.

## Development

```powershell
pip install -e ".[dev]"
ruff check tweetharbor
pytest -q
```

Contribution and security expectations live in [CONTRIBUTING.md](CONTRIBUTING.md) and [SECURITY.md](SECURITY.md).
