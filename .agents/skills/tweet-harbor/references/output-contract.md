# TweetHarbor output contract

## Success envelope

Every successful discovery result contains a versioned schema, request, coverage, ordered articles, warnings, and fetch time. Each article includes its canonical URL, publication basis, eligibility, versioned score, and source evidence. `null` means unknown; it is not zero.

## Error envelope

```json
{
  "status": "error",
  "error": {
    "code": "TIME_WINDOW_UNSUPPORTED",
    "message": "...",
    "remediation": "...",
    "retryable": false
  }
}
```

Important codes: `AUTH_MISSING`, `TIME_WINDOW_UNSUPPORTED`, `UPSTREAM_RATE_LIMITED`, `UPSTREAM_NETWORK_ERROR`, `PROVIDER_UNAVAILABLE`, and `RUN_NOT_FOUND`.

## Provider policy

`fixture` is deterministic offline demonstration data. `x-api` is the official production provider. Agent Reach diagnostics are read-only environment information, not a silent fallback for production queries.
