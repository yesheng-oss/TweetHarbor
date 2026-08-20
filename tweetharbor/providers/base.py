from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from tweetharbor.domain.models import Coverage, DiscoverRequest, EvidencePost


@dataclass(slots=True)
class ProviderResponse:
    posts: list[EvidencePost]
    coverage: Coverage
    warnings: list[str]


class ArticleProvider(Protocol):
    name: str

    def discover(self, request: DiscoverRequest) -> ProviderResponse: ...
