"""Unit tests for the CLI commands."""

import json
import tempfile
import os

import pytest
from click.testing import CliRunner

from modelprobe.cli import main


@pytest.fixture(autouse=True)
def patch_backend(monkeypatch):
    from tests.conftest import NoOpBackend
    import modelprobe.storage.router as router_module
    monkeypatch.setattr(router_module, "_backend", NoOpBackend())
    yield
    monkeypatch.setattr(router_module, "_backend", None)


class TestCLIHelp:
    def test_main_help(self):
        runner = CliRunner()
        result = runner.invoke(main, ["--help"])
        assert result.exit_code == 0
        assert "ModelProbe" in result.output

    def test_version_flag(self):
        runner = CliRunner()
        result = runner.invoke(main, ["--version"])
        assert result.exit_code == 0
        import modelprobe
        assert modelprobe.__version__ in result.output


class TestRunSuiteCommand:
    def test_run_suite_with_valid_json(self):
        cases = [
            {
                "test_case_id": "tc_001",
                "input": "hello",
                "expected_output": "hello",
                "eval_type": "contains",
                "eval_config": {"values": ["hello"]},
            }
        ]
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(cases, f)
            f.flush()
            path = f.name

        runner = CliRunner()
        result = runner.invoke(main, ["run-suite", "test-suite", "-v", "v1", "-f", path])
        os.unlink(path)

        assert result.exit_code == 0
        assert "Pass rate" in result.output

    def test_run_suite_file_not_found(self):
        runner = CliRunner()
        result = runner.invoke(main, ["run-suite", "s", "-v", "v1", "-f", "/nonexistent.json"])
        assert result.exit_code == 1
        assert "not found" in result.output

    def test_run_suite_invalid_json(self):
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            f.write("not valid json{{{")
            path = f.name

        runner = CliRunner()
        result = runner.invoke(main, ["run-suite", "s", "-v", "v1", "-f", path])
        os.unlink(path)

        assert result.exit_code == 1
        assert "Invalid JSON" in result.output

    def test_run_suite_not_array(self):
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump({"not": "an array"}, f)
            path = f.name

        runner = CliRunner()
        result = runner.invoke(main, ["run-suite", "s", "-v", "v1", "-f", path])
        os.unlink(path)

        assert result.exit_code == 1
        assert "JSON array" in result.output

    def test_echo_runner_warning_shown(self):
        cases = [{"test_case_id": "tc_001", "input": "x", "expected_output": "x",
                  "eval_type": "exact", "eval_config": {}}]
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(cases, f)
            path = f.name

        runner = CliRunner()
        result = runner.invoke(main, ["run-suite", "s", "-v", "v1", "-f", path])
        os.unlink(path)

        assert "echo runner" in result.output.lower()


class TestStatusCommand:
    def test_status_shows_version(self):
        runner = CliRunner()
        result = runner.invoke(main, ["status"])
        assert result.exit_code == 0
        assert "ModelProbe" in result.output
        assert "Mode" in result.output
