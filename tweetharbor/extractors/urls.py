from __future__ import annotations

from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

TRACKING_KEYS = {"fbclid", "gclid", "ref", "ref_src", "source", "igshid"}


def canonicalize_url(value: str) -> str | None:
    """Return a deterministic URL identity without marketing parameters."""
    try:
        parts = urlsplit(value.strip())
    except ValueError:
        return None
    if parts.scheme not in {"http", "https"} or not parts.netloc:
        return None
    query = [
        (key, item)
        for key, item in parse_qsl(parts.query, keep_blank_values=True)
        if key.lower() not in TRACKING_KEYS and not key.lower().startswith("utm_")
    ]
    host = parts.netloc.lower()
    if host.startswith("www."):
        host = host[4:]
    path = parts.path.rstrip("/") or "/"
    return urlunsplit((parts.scheme.lower(), host, path, urlencode(sorted(query)), ""))


def is_external_article(url: str) -> bool:
    canonical = canonicalize_url(url)
    if canonical is None:
        return False
    host = urlsplit(canonical).netloc
    return host not in {"x.com", "twitter.com", "t.co"}
