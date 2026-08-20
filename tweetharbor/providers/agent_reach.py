from __future__ import annotations

import json
import shutil
import subprocess


def inspect_agent_reach(timeout: float = 20.0) -> tuple[dict[str, object] | None, list[str]]:
    """Read-only capability inspection; never reads browser cookies or posts content."""
    if shutil.which("agent-reach") is None:
        return None, ["Agent Reach is not installed; experimental local adapters are unavailable."]
    try:
        result = subprocess.run(
            ["agent-reach", "doctor", "--json"],
            capture_output=True,
            timeout=timeout,
            check=False,
        )
        if result.returncode != 0:
            return None, ["Agent Reach doctor did not complete successfully."]
        # Agent Reach emits UTF-8 JSON. Decode explicitly rather than relying
        # on the Windows console code page (which can be GBK).
        report = json.loads(result.stdout.decode("utf-8"))
        twitter = report.get("twitter")
        return {"twitter": twitter, "version_checked": True}, []
    except (OSError, UnicodeDecodeError, subprocess.TimeoutExpired, json.JSONDecodeError):
        return None, ["Agent Reach capability check is unavailable in this environment."]
