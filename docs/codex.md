# Codex integration

## Repository Skill

Codex discovers the repository-level Skill at `.agents/skills/tweet-harbor`. From the repository root, invoke it explicitly with `$tweet-harbor`, or use a matching request such as “找近 7 天 X 上最重要的 AI 文章”.

The Skill runs `tweetharbor doctor --format json` before live requests and keeps coverage warnings in its answer. It never treats fixture results as live X evidence.

## Optional local MCP

Install the optional extra, then add a local STDIO server:

```powershell
pip install -e ".[mcp]"
codex mcp add tweetharbor -- tweetharbor mcp-serve
```

The server exposes `doctor`, `discover_articles`, `get_run`, and the explicit writing tool `save_snapshot`. Do not put tokens in MCP arguments; use `X_BEARER_TOKEN` in the local environment.
