"""Unit tests for the trace decorator."""

import asyncio
import pytest

from modelprobe.trace import trace


def test_sync_callable_writes_run(capturing_backend):
    @trace(suite="test-suite", version="v1")
    def fn(x):
        return x * 2

    result = fn(5)

    assert result == 10
    assert len(capturing_backend.runs) == 1
    run = capturing_backend.runs[0]
    assert run["suite"] == "test-suite"
    assert run["version"] == "v1"
    assert run["status"] == "pass"
    assert run["output"] == "10"
    assert run["trace_id"] is not None
    assert run["parent_id"] is None
    assert run["latency_ms"] >= 0


def test_async_callable_writes_run(capturing_backend):
    @trace(suite="test-suite", version="v1")
    async def async_fn(x):
        return x + 1

    result = asyncio.get_event_loop().run_until_complete(async_fn(10))

    assert result == 11
    assert len(capturing_backend.runs) == 1
    run = capturing_backend.runs[0]
    assert run["status"] == "pass"
    assert run["output"] == "11"


def test_exception_sets_error_status_and_reraises(capturing_backend):
    @trace(suite="test-suite", version="v1")
    def failing_fn():
        raise ValueError("something broke")

    with pytest.raises(ValueError, match="something broke"):
        failing_fn()

    assert len(capturing_backend.runs) == 1
    run = capturing_backend.runs[0]
    assert run["status"] == "error"
    assert "something broke" in run["output"]


def test_tags_are_stored(capturing_backend):
    @trace(suite="test-suite", version="v1", tags={"env": "staging", "feature": "invoice"})
    def fn():
        return "ok"

    fn()

    run = capturing_backend.runs[0]
    assert run["tags"]["env"] == "staging"
    assert run["tags"]["feature"] == "invoice"


def test_storage_failure_does_not_affect_wrapped_function(monkeypatch):
    import modelprobe.storage.router as router_module

    def broken_write(run):
        raise RuntimeError("disk full")

    monkeypatch.setattr(router_module, "write_run", broken_write)

    @trace(suite="test-suite", version="v1")
    def fn(x):
        return x * 3

    result = fn(7)
    assert result == 21


def test_return_value_is_unchanged(capturing_backend):
    @trace(suite="test-suite", version="v1")
    def fn():
        return {"key": "value", "nested": [1, 2, 3]}

    result = fn()
    assert result == {"key": "value", "nested": [1, 2, 3]}
