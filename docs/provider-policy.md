# Provider policy

| Provider | Role | Default | Notes |
|---|---|---:|---|
| `fixture` | Offline demo and contract testing | Yes for local demo | Deterministic; never represent it as live data. |
| `x-api` | Production X post search | Yes for live use | Requires `X_BEARER_TOKEN`; Recent Search is limited to 7 days. |
| Agent Reach | Local capability diagnostics | Diagnostics only | Read-only doctor data is useful; social adapters are not an automatic production fallback. |

Never log Bearer tokens, Cookie values, or raw authorization headers. Do not downgrade to browser automation after a rate limit, access failure, or unsupported time window.
