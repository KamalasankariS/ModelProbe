"""Security tests — API-level security checks.

Verifies CORS configuration, error response safety (no stack traces leaked),
and HTTP method enforcement.
"""

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


class TestErrorResponseSafety:
    """Error responses must not leak internal details."""

    def test_404_does_not_leak_stack_trace(self, client):
        res = client.get("/api/runs/nonexistent-id")
        assert res.status_code == 404
        body = res.text
        assert "Traceback" not in body
        assert "File \"/" not in body

    def test_422_does_not_leak_internals(self, client):
        res = client.post("/api/runs", json={"bad": "data"})
        assert res.status_code == 422
        body = res.text
        assert "Traceback" not in body

    def test_invalid_json_body_returns_422(self, client):
        res = client.post(
            "/api/runs",
            content="not json at all",
            headers={"Content-Type": "application/json"},
        )
        assert res.status_code == 422


class TestHTTPMethodEnforcement:
    """Endpoints must reject incorrect HTTP methods."""

    def test_get_on_post_endpoint(self, client):
        res = client.get("/api/eval-results")
        assert res.status_code == 405

    def test_delete_on_runs(self, client):
        res = client.delete("/api/runs")
        assert res.status_code == 405

    def test_put_on_health(self, client):
        res = client.put("/api/health", json={})
        assert res.status_code == 405


class TestQueryParamSafety:
    """Query parameters must not cause crashes or injection."""

    def test_negative_offset(self, client):
        res = client.get("/api/runs?offset=-1")
        assert res.status_code == 422

    def test_limit_above_max(self, client):
        res = client.get("/api/runs?limit=9999")
        assert res.status_code == 422

    def test_non_numeric_limit(self, client):
        res = client.get("/api/runs?limit=abc")
        assert res.status_code == 422

    def test_empty_tag_value(self, client):
        res = client.get("/api/runs?tag=env:")
        assert res.status_code == 200


class TestCORSHeaders:
    """CORS headers must be present on responses."""

    def test_cors_allows_origin(self, client):
        res = client.options(
            "/api/health",
            headers={
                "Origin": "http://localhost:3000",
                "Access-Control-Request-Method": "GET",
            },
        )
        assert "access-control-allow-origin" in res.headers


class TestEvaluatorInputSafety:
    """Evaluators must not crash on adversarial input."""

    def test_regex_redos_pattern(self):
        """ReDoS-prone patterns should not hang the evaluator."""
        from modelprobe.evaluators.regex import RegexEvaluator
        ev = RegexEvaluator()
        # This pattern + input could cause catastrophic backtracking in naive engines
        # Python's re module handles this case, but we verify it completes
        result = ev.evaluate(
            output="a" * 30,
            config={"pattern": r"(a+)+b"},
        )
        assert result["passed"] is False
        assert result["status"] == "fail"

    def test_json_schema_with_huge_schema(self):
        """Large schemas should not crash the evaluator."""
        from modelprobe.evaluators.json_schema import JsonSchemaEvaluator
        ev = JsonSchemaEvaluator()
        schema = {
            "type": "object",
            "properties": {f"field_{i}": {"type": "string"} for i in range(500)},
        }
        result = ev.evaluate(output='{"field_0": "val"}', config={"schema": schema})
        assert result["status"] == "pass"
