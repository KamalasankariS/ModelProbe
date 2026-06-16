"""Unit tests for the POST /api/evaluate endpoint."""

import asyncio
import os
import tempfile

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
        loop = asyncio.new_event_loop()
        loop.run_until_complete(db_module._engine.dispose())
        loop.close()
    db_module._engine = None
    db_module._session_factory = None
    os.unlink(db_path)
    os.environ.pop("DATABASE_URL", None)


class TestContainsEvaluator:

    def test_contains_pass(self, client):
        res = client.post("/api/evaluate", json={
            "output": "The invoice total is $500",
            "eval_type": "contains",
            "config": {"values": ["invoice", "$500"], "mode": "all"},
        })
        assert res.status_code == 200
        data = res.json()["data"]
        assert data["passed"] is True
        assert data["score"] == 1.0
        assert data["status"] == "pass"
        assert data["evaluator"] == "contains"

    def test_contains_fail(self, client):
        res = client.post("/api/evaluate", json={
            "output": "hello world",
            "eval_type": "contains",
            "config": {"values": ["missing"], "mode": "any"},
        })
        assert res.status_code == 200
        data = res.json()["data"]
        assert data["passed"] is False
        assert data["score"] == 0.0
        assert data["status"] == "fail"


class TestExactEvaluator:

    def test_exact_pass(self, client):
        res = client.post("/api/evaluate", json={
            "output": "Hello",
            "eval_type": "exact",
            "expected": "Hello",
        })
        assert res.status_code == 200
        data = res.json()["data"]
        assert data["passed"] is True
        assert data["score"] == 1.0

    def test_exact_fail(self, client):
        res = client.post("/api/evaluate", json={
            "output": "Hello",
            "eval_type": "exact",
            "expected": "Goodbye",
        })
        assert res.status_code == 200
        data = res.json()["data"]
        assert data["passed"] is False


class TestRegexEvaluator:

    def test_regex_pass(self, client):
        res = client.post("/api/evaluate", json={
            "output": "Order #12345 confirmed",
            "eval_type": "regex",
            "config": {"pattern": "Order #\\d+"},
        })
        assert res.status_code == 200
        data = res.json()["data"]
        assert data["passed"] is True

    def test_regex_fail(self, client):
        res = client.post("/api/evaluate", json={
            "output": "No order here",
            "eval_type": "regex",
            "config": {"pattern": "Order #\\d+"},
        })
        assert res.status_code == 200
        data = res.json()["data"]
        assert data["passed"] is False


class TestJsonSchemaEvaluator:

    def test_json_schema_pass(self, client):
        res = client.post("/api/evaluate", json={
            "output": '{"name": "Alice", "age": 30}',
            "eval_type": "json_schema",
            "config": {
                "schema": {
                    "type": "object",
                    "required": ["name"],
                    "properties": {"name": {"type": "string"}},
                }
            },
        })
        assert res.status_code == 200
        data = res.json()["data"]
        assert data["passed"] is True

    def test_json_schema_invalid_json(self, client):
        res = client.post("/api/evaluate", json={
            "output": "not json",
            "eval_type": "json_schema",
            "config": {"schema": {"type": "object"}},
        })
        assert res.status_code == 200
        data = res.json()["data"]
        assert data["passed"] is False


class TestErrorCases:

    def test_invalid_eval_type(self, client):
        res = client.post("/api/evaluate", json={
            "output": "test",
            "eval_type": "nonexistent",
        })
        assert res.status_code == 200
        data = res.json()["data"]
        assert data["passed"] is False
        assert data["status"] == "error"

    def test_missing_output_returns_422(self, client):
        res = client.post("/api/evaluate", json={
            "eval_type": "exact",
            "expected": "hello",
        })
        assert res.status_code == 422


class TestResponseEnvelope:

    def test_envelope_structure(self, client):
        res = client.post("/api/evaluate", json={
            "output": "hello",
            "eval_type": "exact",
            "expected": "hello",
        })
        assert res.status_code == 200
        body = res.json()
        assert "data" in body
        assert "version" in body
        assert "timestamp" in body
        assert isinstance(body["version"], str)
