---
name: tweet-harbor
description: Discover and rank important external articles shared on X/Twitter with evidence and coverage disclosure. Use when Codex is asked to find the hottest, most important, or most worth-reading AI, agent, LLM, security, or developer articles on X from a recent time window, or to inspect a saved TweetHarbor result. Do not use for posting, liking, replying, generic web summaries, or GitHub-only repository rankings.
---

# TweetHarbor

Use TweetHarbor to return an evidence-first article list. Treat coverage as part of the answer: never describe a partial query as complete and never present fixture data as live X results.

## Workflow

1. Run `tweetharbor doctor --format json` before a live X request.
2. If `x_api_configured` is true, run `tweetharbor discover "<topic>" --days <1-10> --provider x-api --format json`.
3. If the X API is unavailable, explain the missing credential. Run `--provider fixture` only for a demo, test, or offline example and label it as fixture data.
4. Read `references/output-contract.md` before interpreting fields, errors, or coverage.
5. Present title, direct URL, score, evidence-post count, coverage status, and warnings.
6. Use `--save` or `tweetharbor snapshot` only when the user explicitly asks to persist a run. Use `tweetharbor get-run <id>` for a saved run.

## Coverage rules

- Recent Search can cover no more than 7 days. A 10-day request needs Full-Archive access; otherwise report `TIME_WINDOW_UNSUPPORTED` or the partial result exactly as returned.
- Preserve `null` as unknown; do not turn unknown engagement, dates, or coverage into zero.
- Exclude `uncertain_date` articles from the main list unless the user asks to include them.
- Do not silently replace an official API failure with browser automation, Agent Reach social adapters, or unrelated GitHub results.

## Response format

Answer in Chinese unless asked otherwise. State the number of eligible articles and `coverage.status` first. Include direct links and evidence-post counts. If the result is fixture data, begin with “离线演示数据”. Keep warnings concise and explicit.

## MCP preference

If the local `tweetharbor` MCP server is configured, call its read-only `doctor` and `discover_articles` tools. Otherwise use the CLI JSON contract. Never parse the Rich output from the legacy `starscout` command.
