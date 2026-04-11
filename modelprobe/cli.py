"""ModelProbe command-line interface."""

from __future__ import annotations

import json
import sys
from pathlib import Path

import click


@click.group()
@click.version_option(package_name="modelprobe")
def main():
    """ModelProbe — AI evaluation and regression testing platform."""


@main.command()
@click.option("--host", default="0.0.0.0", show_default=True, help="Bind host.")
@click.option("--port", default=8000, show_default=True, help="Bind port.")
@click.option("--reload", is_flag=True, default=False, help="Enable auto-reload (dev only).")
def start(host: str, port: int, reload: bool):
    """Start the ModelProbe dashboard and REST API server.

    Requires the [server] extras::

        pip install modelprobe[server]
        modelprobe start --port 8000
    """
    try:
        import uvicorn
        from modelprobe.server.main import create_app
    except ImportError:
        click.echo(
            "The server extras are not installed.\n"
            "Run:  pip install modelprobe[server]",
            err=True,
        )
        sys.exit(1)

    app = create_app()
    click.echo(f"ModelProbe server starting on http://{host}:{port}")
    uvicorn.run(app, host=host, port=port, reload=reload)


@main.command()
def migrate():
    """Run database migrations using Alembic.

    Requires the [server] extras::

        pip install modelprobe[server]
        modelprobe migrate
    """
    try:
        from alembic.config import Config
        from alembic import command
    except ImportError:
        click.echo(
            "Alembic is not installed.\n"
            "Run:  pip install modelprobe[server]",
            err=True,
        )
        sys.exit(1)

    migrations_dir = Path(__file__).parent / "server" / "db" / "migrations"
    cfg = Config()
    cfg.set_main_option("script_location", str(migrations_dir))
    command.upgrade(cfg, "head")
    click.echo("Migrations applied.")


@main.command("run-suite")
@click.argument("suite")
@click.option("--version", "-v", required=True, help="Suite version string.")
@click.option("--file", "-f", "test_file", required=True, help="Path to JSON test cases file.")
@click.option("--run-group", default=None, help="Optional run group label.")
@click.option("--commit", default=None, help="Optional git commit hash.")
def run_suite_cmd(suite: str, version: str, test_file: str, run_group: str, commit: str):
    """Run a suite from a JSON test cases file.

    The JSON file must be a list of test case objects::

        [
          {
            "test_case_id": "tc_001",
            "input": "...",
            "expected_output": "...",
            "eval_type": "contains",
            "eval_config": {"values": ["..."]}
          }
        ]

    Usage::

        modelprobe run-suite my-agent --version v2 --file cases.json
    """
    path = Path(test_file)
    if not path.exists():
        click.echo(f"File not found: {test_file}", err=True)
        sys.exit(1)

    try:
        test_cases = json.loads(path.read_text())
    except json.JSONDecodeError as exc:
        click.echo(f"Invalid JSON in {test_file}: {exc}", err=True)
        sys.exit(1)

    if not isinstance(test_cases, list):
        click.echo("Test cases file must contain a JSON array.", err=True)
        sys.exit(1)

    from modelprobe.suite import run_suite

    click.echo(f"Running suite '{suite}' version '{version}' with {len(test_cases)} test case(s)...")

    result = run_suite(
        suite_name=suite,
        version=version,
        test_cases=test_cases,
        runner=lambda tc: tc.get("input", ""),
        run_group=run_group,
        commit_hash=commit,
    )

    click.echo(f"\nResults for {suite} @ {version}")
    click.echo(f"  Total:   {result.total}")
    click.echo(f"  Passed:  {result.passed}")
    click.echo(f"  Failed:  {result.failed}")
    click.echo(f"  Errored: {result.errored}")
    click.echo(f"  Skipped: {result.skipped}")
    click.echo(f"  Pass rate: {result.pass_rate:.1%}")

    if result.failed > 0 or result.errored > 0:
        sys.exit(1)


@main.command()
def status():
    """Print current ModelProbe configuration and connection status.

    Usage::

        modelprobe status
    """
    from modelprobe.config import settings
    import modelprobe

    click.echo(f"ModelProbe v{modelprobe.__version__}")
    click.echo(f"  Mode:    {settings.mode}")

    if settings.mode == "local":
        click.echo(f"  DB:      {settings.db_path}")
        db_exists = Path(settings.db_path).exists()
        click.echo(f"  DB file: {'exists' if db_exists else 'will be created on first write'}")
    else:
        click.echo(f"  Server:  {settings.server}")
        try:
            import httpx
            resp = httpx.get(f"{settings.server}/api/health", timeout=5.0)
            resp.raise_for_status()
            health = resp.json().get("data", {})
            click.echo(f"  Health:  OK (uptime {health.get('uptime_s', '?')}s)")
        except Exception as exc:
            click.echo(f"  Health:  UNREACHABLE ({exc})")

    click.echo(f"  LLM endpoint: {settings.llm_endpoint}")
