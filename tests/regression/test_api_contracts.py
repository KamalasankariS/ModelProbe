"""API response envelope and endpoint contracts."""

import os
import tempfile
from datetime import datetime, timezone
from uuid import uuid4

import pytest

pytest.importorskip("fastapi")
pytest.importorskip("httpx")

from fastapi.testclient import TestClient


@pytest.fixture
def client():
    from modelprobe.server.db import database as db_module

    db_module._engine = None
    db_module._session_factory = None

    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        db_path = f.name

    os.environ["DATABASE_URL"] = f"sqlite+aiosqlite:///{db_path}"

    from modelprobe.server.main import create_app
    app = create_app()

    with TestClient(app, raise_server_exceptions=True) as c:
        yield c

    if db_module._engine is not None:
        import asyncio
        loop = asyncio.new_event_loop()
        loop.run_until_complete(db_module._engine.dispose())
        loop.close()
    db_module._engine = None
    db_module._session_factory = None
    os.unlink(db_path)
    os.environ.pop("DATABASE_URL", None)


def _submit_run(client, suite="s", version="v1", status="pass"):
    payload = {
        "id": str(uuid4()),
        "trace_id": str(uuid4()),
        "suite": suite,
        "version": version,
        "input": "in",
        "output": "out",
        "status": status,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
    res = client.post("/api/runs", json=payload)
    assert res.status_code == 201
    return payload


ENVELOPE_KEYS = {"data", "version", "timestamp", "request_id"}


class TestEnvelopeShape:
    """Every endpoint must return the standard APIEnvelope."""

    def test_health_envelope(self, client):
        body = client.get("/api/health").json()
        assert ENVELOPE_KEYS.issubset(body.keys())

    def test_runs_list_envelope(self, client):
        body = client.get("/api/runs").json()
        assert ENVELOPE_KEYS.issubset(body.keys())
        assert isinstance(body["data"], list)

    def test_run_submit_envelope(self, client):
        payload = {
            "id": str(uuid4()), "trace_id": str(uuid4()),
            "suite": "s", "version": "v1", "status": "pass",
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
        body = client.post("/api/runs", json=payload).json()
        assert ENVELOPE_KEYS.issubset(body.keys())

    def test_suites_list_envelope(self, client):
        _submit_run(client)
        body = client.get("/api/suites").json()
        assert ENVELOPE_KEYS.issubset(body.keys())
        assert isinstance(body["data"], list)


class TestRunRecordShape:
    """A run record must always have the documented fields."""

    RUN_KEYS = {
        "id", "trace_id", "parent_id", "suite", "version",
        "run_group", "commit_hash", "tags", "input", "output",
        "status", "latency_ms", "token_count", "timestamp", "steps",
    }

    def test_submitted_run_has_all_fields(self, client):
        run = _submit_run(client)
        body = client.get(f"/api/runs/{run['id']}").json()
        assert self.RUN_KEYS.issubset(body["data"].keys())

    def test_steps_is_list(self, client):
        run = _submit_run(client)
        body = client.get(f"/api/runs/{run['id']}").json()
        assert isinstance(body["data"]["steps"], list)

    def test_tags_is_dict(self, client):
        run = _submit_run(client)
        body = client.get(f"/api/runs/{run['id']}").json()
        assert isinstance(body["data"]["tags"], dict)


class TestHealthShape:
    """Health endpoint must return version, mode, db_status, uptime_s."""

    def test_health_data_fields(self, client):
        data = client.get("/api/health").json()["data"]
        assert "version" in data
        assert "mode" in data
        assert "db_status" in data
        assert "uptime_s" in data


class TestCompareShape:
    """Compare endpoint must return regressed/improved/unchanged/new/removed."""

    COMPARE_KEYS = {"suite", "v1", "v2", "regressed", "improved", "unchanged", "new", "removed"}

    def test_compare_has_all_diff_keys(self, client):
        _submit_run(client, suite="cs", version="v1")
        _submit_run(client, suite="cs", version="v2")
        body = client.get("/api/suites/cs/compare?v1=v1&v2=v2").json()
        assert self.COMPARE_KEYS.issubset(body["data"].keys())
