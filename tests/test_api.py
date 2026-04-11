"""Tests for API endpoints — compare diff shape and regression detection."""

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

    db_module._engine = None
    db_module._session_factory = None
    os.unlink(db_path)
    os.environ.pop("DATABASE_URL", None)


def _submit_run(client, suite, version, trace_id=None, status="pass"):
    tid = trace_id or str(uuid4())
    payload = {
        "id": str(uuid4()),
        "trace_id": tid,
        "suite": suite,
        "version": version,
        "input": "test input",
        "output": "test output",
        "status": status,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
    res = client.post("/api/runs", json=payload)
    assert res.status_code == 201, res.text
    return payload


def _submit_eval(client, run_id, tc_id, status="pass", score=1.0):
    payload = {
        "id": str(uuid4()),
        "run_id": run_id,
        "test_case_id": tc_id,
        "passed": status == "pass",
        "score": score,
        "reason": f"status is {status}",
        "status": status,
        "evaluator": "exact",
    }
    res = client.post("/api/eval-results", json=payload)
    assert res.status_code == 201, res.text
    return payload


def test_health_endpoint(client):
    res = client.get("/api/health")
    assert res.status_code == 200
    data = res.json()
    assert "data" in data
    assert "version" in data["data"]
    assert "timestamp" in data
    assert "request_id" in data


def test_submit_and_retrieve_run(client):
    run = _submit_run(client, "suite-a", "v1")
    res = client.get(f"/api/runs/{run['id']}")
    assert res.status_code == 200
    data = res.json()["data"]
    assert data["id"] == run["id"]
    assert data["suite"] == "suite-a"


def test_list_runs_filter_by_suite(client):
    _submit_run(client, "suite-x", "v1")
    _submit_run(client, "suite-y", "v1")

    res = client.get("/api/runs?suite=suite-x")
    assert res.status_code == 200
    data = res.json()["data"]
    assert all(r["suite"] == "suite-x" for r in data)


def test_compare_endpoint_regression_shape(client):
    tc_id = "tc_001"
    suite = "compare-suite"

    run_v1 = _submit_run(client, suite, "v1")
    _submit_eval(client, run_v1["id"], tc_id, status="pass", score=1.0)

    run_v2 = _submit_run(client, suite, "v2")
    _submit_eval(client, run_v2["id"], tc_id, status="fail", score=0.0)

    res = client.get(f"/api/suites/{suite}/compare?v1=v1&v2=v2")
    assert res.status_code == 200
    diff = res.json()["data"]

    assert "regressed" in diff
    assert "improved" in diff
    assert "unchanged" in diff
    assert "new" in diff
    assert "removed" in diff

    assert len(diff["regressed"]) == 1
    assert diff["regressed"][0]["test_case_id"] == tc_id
    assert diff["regressed"][0]["v1_status"] == "pass"
    assert diff["regressed"][0]["v2_status"] == "fail"


def test_compare_endpoint_improvement_shape(client):
    tc_id = "tc_improved"
    suite = "improve-suite"

    run_v1 = _submit_run(client, suite, "v1")
    _submit_eval(client, run_v1["id"], tc_id, status="fail", score=0.0)

    run_v2 = _submit_run(client, suite, "v2")
    _submit_eval(client, run_v2["id"], tc_id, status="pass", score=1.0)

    res = client.get(f"/api/suites/{suite}/compare?v1=v1&v2=v2")
    assert res.status_code == 200
    diff = res.json()["data"]
    assert len(diff["improved"]) == 1
    assert diff["improved"][0]["test_case_id"] == tc_id


def test_regressions_endpoint_empty_for_single_version(client):
    _submit_run(client, "single-version-suite", "v1")
    res = client.get("/api/suites/single-version-suite/regressions")
    assert res.status_code == 200
    assert res.json()["data"] == []


def test_run_not_found_returns_404(client):
    res = client.get("/api/runs/does-not-exist")
    assert res.status_code == 404


def test_response_envelope_structure(client):
    run = _submit_run(client, "env-suite", "v1")
    res = client.get(f"/api/runs/{run['id']}")
    body = res.json()
    assert "data" in body
    assert "version" in body
    assert "timestamp" in body
    assert "request_id" in body
