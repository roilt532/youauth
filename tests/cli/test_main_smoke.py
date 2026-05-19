from __future__ import annotations

import typer.testing

from alvaro.cli.main import app

_runner = typer.testing.CliRunner()


def test_help_lists_commands() -> None:
    result = _runner.invoke(app, ["--help"])
    assert result.exit_code == 0
    for cmd in ("generate", "upload", "analytics", "version"):
        assert cmd in result.output


def test_generate_help() -> None:
    result = _runner.invoke(app, ["generate", "--help"])
    assert result.exit_code == 0


def test_upload_help() -> None:
    result = _runner.invoke(app, ["upload", "--help"])
    assert result.exit_code == 0


def test_analytics_help() -> None:
    result = _runner.invoke(app, ["analytics", "--help"])
    assert result.exit_code == 0
