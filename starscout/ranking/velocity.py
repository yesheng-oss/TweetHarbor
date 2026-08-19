from __future__ import annotations


def safe_growth_rate(delta: int | None, base: int | None) -> float | None:
    if delta is None or base is None or base <= 0:
        return None
    return delta / base


def normalize(value: float, cap: float) -> float:
    if cap <= 0:
        return 0.0
    return max(0.0, min(value / cap, 1.0))
