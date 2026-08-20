from __future__ import annotations

from tweetharbor.domain.models import DiscoveryResult


def render_json(result: DiscoveryResult) -> str:
    return result.model_dump_json(indent=2)


def _cell(value: str) -> str:
    return value.replace("|", "\\|").replace("\n", " ")


def render_markdown(result: DiscoveryResult) -> str:
    coverage = result.coverage
    lines = [
        f"# TweetHarbor: {result.request.topic}",
        "",
        f"- Status: `{result.status}`",
        f"- Coverage: `{coverage.status}` ({coverage.actual_from or 'unknown'} → {coverage.actual_to or 'unknown'})",
        f"- Provider: {', '.join(coverage.providers) or 'unknown'}",
        "- Score version: `article-v1`",
        "",
        "| # | Article | Score | Evidence | Coverage note |",
        "|---:|---|---:|---:|---|",
    ]
    for article in result.items:
        score = article.score.final if article.score else 0
        note = article.eligibility
        lines.append(
            f"| {article.rank or '-'} | [{_cell(article.title)}]({article.canonical_url}) | "
            f"{score:.2f} | {len(article.evidence_posts)} posts | {_cell(note)} |"
        )
    if not result.items:
        lines.append("| - | No eligible external articles found. | - | - | - |")
    if result.warnings:
        lines.extend(["", "## Warnings", ""])
        lines.extend(f"- {warning}" for warning in result.warnings)
    return "\n".join(lines) + "\n"
