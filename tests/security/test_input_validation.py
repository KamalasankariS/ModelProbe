"""Input validation: malformed payloads, special characters, oversized inputs."""

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


class TestMalformedPayloads:
    def test_empty_body_rejected(self, client):
        res = client.post("/api/runs", json={})
        assert res.status_code == 422

    def test_missing_required_fields(self, client):
        res = client.post("/api/runs", json={"id": str(uuid4())})
        assert res.status_code == 422

    def test_invalid_status_rejected(self, client):
        payload = {
            "id": str(uuid4()), "trace_id": str(uuid4()),
            "suite": "s", "version": "v1",
            "status": "INVALID_STATUS",
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
        res = client.post("/api/runs", json=payload)
        assert res.status_code == 422

    def test_eval_result_missing_run_id(self, client):
        res = client.post("/api/eval-results", json={
            "test_case_id": "tc_001", "passed": True,
            "evaluator": "exact",
        })
        assert res.status_code == 422


class TestSpecialCharacters:
    def test_suite_name_with_special_chars(self, client):
        payload = {
            "id": str(uuid4()), "trace_id": str(uuid4()),
            "suite": "suite-with/special<chars>&more",
            "version": "v1", "status": "pass",
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
        res = client.post("/api/runs", json=payload)
        assert res.status_code == 201
        data = res.json()["data"]
        assert data["suite"] == "suite-with/special<chars>&more"

    def test_unicode_in_input_output(self, client):
        payload = {
            "id": str(uuid4()), "trace_id": str(uuid4()),
            "suite": "unicode-test", "version": "v1",
            "input": "Hello \u4e16\u754c",
            "output": "Response: \u00e9\u00e8\u00ea\u00eb",
            "status": "pass",
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
        res = client.post("/api/runs", json=payload)
        assert res.status_code == 201

    def test_null_bytes_in_input(self, client):
        payload = {
            "id": str(uuid4()), "trace_id": str(uuid4()),
            "suite": "null-test", "version": "v1",
            "input": "before\x00after",
            "output": "output",
            "status": "pass",
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
        res = client.post("/api/runs", json=payload)
        assert res.status_code in (201, 422)


class TestOversizedInputs:
    def test_very_long_input(self, client):
        payload = {
            "id": str(uuid4()), "trace_id": str(uuid4()),
            "suite": "long-test", "version": "v1",
            "input": "x" * 100_000,
            "output": "y" * 100_000,
            "status": "pass",
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
        res = client.post("/api/runs", json=payload)
        assert res.status_code == 201

    def test_deeply_nested_tags(self, client):
        payload = {
            "id": str(uuid4()), "trace_id": str(uuid4()),
            "suite": "tags-test", "version": "v1",
            "tags": {f"key_{i}": f"val_{i}" for i in range(100)},
            "status": "pass",
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
        res = client.post("/api/runs", json=payload)
        assert res.status_code == 201


class TestPathTraversal:
    def test_run_id_with_path_chars(self, client):
        res = client.get("/api/runs/../../etc/passwd")
        assert res.status_code == 404

    def test_suite_name_with_path_chars(self, client):
        res = client.get("/api/suites/../../etc/passwd")
        assert res.status_code == 404
