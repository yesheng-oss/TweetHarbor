# Security policy

Report suspected credential exposure or data-handling flaws privately to the maintainers. Do not include live tokens, browser cookies, or private X content in an issue.

TweetHarbor stores only explicit local SQLite snapshots. It does not need and must not attempt to read browser cookie stores. Use environment variables for API credentials and rotate any credential accidentally exposed in logs or commits.
