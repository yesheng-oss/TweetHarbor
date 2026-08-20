from __future__ import annotations

from dataclasses import dataclass


@dataclass(slots=True)
class TweetHarborError(RuntimeError):
    """A safe, structured error that can be rendered by CLI or MCP."""

    code: str
    message: str
    remediation: str | None = None
    retryable: bool = False

    def __str__(self) -> str:
        return self.message

    def as_dict(self) -> dict[str, object]:
        return {
            "code": self.code,
            "message": self.message,
            "remediation": self.remediation,
            "retryable": self.retryable,
        }
