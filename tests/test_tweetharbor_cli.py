import json

from typer.testing import CliRunner

from tweetharbor.cli import app

runner = CliRunner()


def test_cli_emits_parseable_json_and_only_saves_when_requested(tmp_path) -> None:
    db_path = tmp_path / "harbor.db"
    result = runner.invoke(
        app,
        [
            "--db-path",
            str(db_path),
            "discover",
            "AI Agent",
            "--days",
            "10",
            "--provider",
            "fixture",
            "--format",
            "json",
            "--save",
        ],
    )

    assert result.exit_code == 0, result.output
    payload = json.loads(result.output)
    assert payload["status"] == "ok"
    assert payload["items"][0]["rank"] == 1

    fetched = runner.invoke(app, ["--db-path", str(db_path), "get-run", payload["run_id"]])
    assert fetched.exit_code == 0
    assert json.loads(fetched.output)["run_id"] == payload["run_id"]


def test_cli_reports_x_window_error_as_json(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("X_BEARER_TOKEN", "test-token")
    result = runner.invoke(
        app,
        [
            "--db-path",
            str(tmp_path / "harbor.db"),
            "discover",
            "AI Agent",
            "--days",
            "10",
            "--provider",
            "x-api",
            "--format",
            "json",
        ],
    )

    assert result.exit_code == 2
    assert json.loads(result.output)["error"]["code"] == "TIME_WINDOW_UNSUPPORTED"
