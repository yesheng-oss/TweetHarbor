# Architecture

TweetHarbor separates interfaces from application logic. The CLI, Codex Skill, and optional MCP server all call `DiscoveryService`; none is allowed to parse another interface's output.

```text
CLI / Skill / MCP
        │
DiscoveryService
  ├── Provider contract (fixture, official X API)
  ├── URL canonicalization and exact deduplication
  ├── deterministic article-v1 ranking
  └── SQLite query-run repository
```

Providers return evidence posts and coverage only. The application layer decides external-article eligibility and ranking. This keeps provider failures visible and makes fixture results reproducible.

## Read/write boundary

`discover` is read-only by default. `discover --save` and `snapshot` are the only CLI writes. In MCP, `save_snapshot` is deliberately a separate tool.

## Coverage boundary

Full coverage requires every requested time slice and page to complete. The project reports the provider's actual window, page count, candidate cap, and degradation reasons. A 10-day X request requires Full-Archive access; Recent Search alone cannot satisfy it.
