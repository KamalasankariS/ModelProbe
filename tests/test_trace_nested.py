"""Tests for nested trace context stack producing correct trace_id/parent_id trees."""

import pytest
from modelprobe.trace import trace


class _CapturingBackend:
    def __init__(self):
        self.runs = []

    def write_run(self, run):
        self.runs.append(dict(run))

    def get_run(self, run_id):
        return next((r for r in self.runs if r["id"] == run_id), None)

    def list_runs(self, filters=None):
        return list(self.runs)

    def write_eval_result(self, result):
        pass

    def write_test_case(self, tc):
        pass

    def list_test_cases(self, suite):
        return []

    def list_eval_results(self, run_id):
        return []

    def list_suites(self):
        return []


@pytest.fixture(autouse=True)
def capture_backend(monkeypatch):
    backend = _CapturingBackend()
    import modelprobe.storage.router as router_module
    monkeypatch.setattr(router_module, "_backend", backend)
    yield backend
    monkeypatch.setattr(router_module, "_backend", None)


def test_nested_traces_share_trace_id(capture_backend):
    @trace(suite="agent", version="v1")
    def child_a():
        return "a"

    @trace(suite="agent", version="v1")
    def child_b():
        return "b"

    @trace(suite="agent", version="v1")
    def root():
        child_a()
        child_b()
        return "root"

    root()

    runs = capture_backend.runs
    assert len(runs) == 3

    root_run = next(r for r in runs if r["output"] == "root")
    a_run = next(r for r in runs if r["output"] == "a")
    b_run = next(r for r in runs if r["output"] == "b")

    assert root_run["parent_id"] is None
    assert a_run["parent_id"] == root_run["id"]
    assert b_run["parent_id"] == root_run["id"]

    assert a_run["trace_id"] == root_run["trace_id"]
    assert b_run["trace_id"] == root_run["trace_id"]


def test_deeply_nested_traces(capture_backend):
    @trace(suite="agent", version="v1")
    def level3():
        return "deep"

    @trace(suite="agent", version="v1")
    def level2():
        return level3()

    @trace(suite="agent", version="v1")
    def level1():
        return level2()

    level1()

    runs = capture_backend.runs
    assert len(runs) == 3

    l1 = next(r for r in runs if r["parent_id"] is None)
    l2 = next(r for r in runs if r["parent_id"] == l1["id"])
    l3 = next(r for r in runs if r["parent_id"] == l2["id"])

    assert l1["trace_id"] == l2["trace_id"] == l3["trace_id"]
    assert l3["output"] == "deep"


def test_independent_calls_have_different_trace_ids(capture_backend):
    @trace(suite="agent", version="v1")
    def standalone(x):
        return x

    standalone("first")
    standalone("second")

    runs = capture_backend.runs
    assert len(runs) == 2
    assert runs[0]["trace_id"] != runs[1]["trace_id"]
    assert runs[0]["parent_id"] is None
    assert runs[1]["parent_id"] is None
