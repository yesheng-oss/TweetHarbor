import json
from types import SimpleNamespace

from tweetharbor.providers.agent_reach import inspect_agent_reach


def test_agent_reach_diagnostics_decodes_utf8_json(monkeypatch) -> None:
    payload = {"twitter": {"status": "warn", "message": "已配置"}}
    monkeypatch.setattr("tweetharbor.providers.agent_reach.shutil.which", lambda _: "agent-reach")
    monkeypatch.setattr(
        "tweetharbor.providers.agent_reach.subprocess.run",
        lambda *args, **kwargs: SimpleNamespace(returncode=0, stdout=json.dumps(payload).encode("utf-8")),
    )

    report, warnings = inspect_agent_reach()

    assert warnings == []
    assert report == {"twitter": payload["twitter"], "version_checked": True}
