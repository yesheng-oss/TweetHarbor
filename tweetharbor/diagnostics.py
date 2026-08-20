from __future__ import annotations

import os
from pathlib import Path

from tweetharbor.domain.models import DoctorReport
from tweetharbor.providers.agent_reach import inspect_agent_reach


def build_doctor_report(database_path: str | Path) -> DoctorReport:
    agent_reach, warnings = inspect_agent_reach()
    if not os.getenv("X_BEARER_TOKEN"):
        warnings.append("X_BEARER_TOKEN is not configured; live X API queries are unavailable.")
    return DoctorReport(
        x_api_configured=bool(os.getenv("X_BEARER_TOKEN")),
        agent_reach=agent_reach,
        database_path=str(database_path),
        supported_providers=["fixture", "x-api"],
        warnings=warnings,
    )
