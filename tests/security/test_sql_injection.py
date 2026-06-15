"""Security tests — SQL injection attack vectors.

Verifies that tag filtering, user inputs, and query parameters
cannot be used to inject arbitrary SQL into database queries.
"""

import os
import tempfile
import pytest

from modelprobe.storage.sqlite import SQLiteBackend

pytest.importorskip("fastapi")
pytest.importorskip("httpx")

from fastapi.testclient import TestClient


# ---------------------------------------------------------------
# SQLite backend — tag filter injection
# ---------------------------------------------------------------

@pytest.fixture
def backend():
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        db_path = f.name
    b = SQLiteBackend(db_path)
    b.write_run({
        "id": "r1", "trace_id": "t1", "suite": "s", "version": "v1",
        "tags": {"env": "prod"}, "input": "x", "output": "y", "status": "pass",
    })
    yield b
    os.unlink(db_path)


SQL_INJECTION_PAYLOADS = [
    "env') OR 1=1 --:anything",
    "env'; DROP TABLE runs; --:x",
    "env') UNION SELECT * FROM runs --:x",
    "env\"; DROP TABLE runs; --:x",
    "env' OR '1'='1:x",
    "') OR ('1'='1:x",
    "env${IFS}OR${IFS}1=1:x",
    "env/**/OR/**/1=1:x",
]


@pytest.mark.parametrize("payload", SQL_INJECTION_PAYLOADS)
def test_sqlite_tag_filter_rejects_injection(backend, payload):
    """Malicious tag keys must be rejected, not interpolated into SQL."""
    results = backend.list_runs({"tag": payload})
    # Should return empty — not all rows, not an error
    assert results == []


def test_sqlite_tag_filter_allows_valid_keys(backend):
    """Valid tag keys must still work after the security fix."""
    results = backend.list_runs({"tag": "env:prod"})
    assert len(results) == 1
    assert results[0]["tags"]["env"] == "prod"


def test_sqlite_tag_filter_rejects_dot_traversal(backend):
    """JSON path traversal via dots must be blocked."""
    results = backend.list_runs({"tag": "env.nested.key:value"})
    assert results == []


def test_sqlite_tag_value_with_special_chars(backend):
    """Tag values with SQL metacharacters must be safely parameterized."""
    results = backend.list_runs({"tag": "env:prod' OR '1'='1"})
    assert results == []


# ---------------------------------------------------------------
# API endpoint — tag filter injection via query parameter
# ---------------------------------------------------------------

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


API_INJECTION_PAYLOADS = [
    "env') OR 1=1 --:x",
    "env'; DROP TABLE runs; --:x",
    "env') UNION SELECT * FROM runs --:x",
    "env' OR '1'='1:x",
]


@pytest.mark.parametrize("payload", API_INJECTION_PAYLOADS)
def test_api_tag_filter_rejects_injection(client, payload):
    """API tag query param must reject SQL injection attempts."""
    res = client.get(f"/api/runs?tag={payload}")
    assert res.status_code == 200
    data = res.json()["data"]
    assert data == []


def test_api_tag_filter_allows_valid_key(client):
    """Valid tag queries must still work through the API."""
    from datetime import datetime, timezone
    from uuid import uuid4

    payload = {
        "id": str(uuid4()), "trace_id": str(uuid4()),
        "suite": "sec-test", "version": "v1",
        "tags": {"env": "staging"}, "status": "pass",
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
    client.post("/api/runs", json=payload)

    res = client.get("/api/runs?tag=env:staging")
    assert res.status_code == 200
    data = res.json()["data"]
    assert len(data) == 1
    assert data[0]["tags"]["env"] == "staging"
