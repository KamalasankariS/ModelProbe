"""Unit tests for nested trace context — trace_id/parent_id tree correctness."""

from modelprobe.trace import trace


def test_nested_traces_share_trace_id(capturing_backend):
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

    runs = capturing_backend.runs
    assert len(runs) == 3

    root_run = next(r for r in runs if r["output"] == "root")
    a_run = next(r for r in runs if r["output"] == "a")
    b_run = next(r for r in runs if r["output"] == "b")

    assert root_run["parent_id"] is None
    assert a_run["parent_id"] == root_run["id"]
    assert b_run["parent_id"] == root_run["id"]

    assert a_run["trace_id"] == root_run["trace_id"]
    assert b_run["trace_id"] == root_run["trace_id"]


def test_deeply_nested_traces(capturing_backend):
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

    runs = capturing_backend.runs
    assert len(runs) == 3

    l1 = next(r for r in runs if r["parent_id"] is None)
    l2 = next(r for r in runs if r["parent_id"] == l1["id"])
    l3 = next(r for r in runs if r["parent_id"] == l2["id"])

    assert l1["trace_id"] == l2["trace_id"] == l3["trace_id"]
    assert l3["output"] == "deep"


def test_independent_calls_have_different_trace_ids(capturing_backend):
    @trace(suite="agent", version="v1")
    def standalone(x):
        return x

    standalone("first")
    standalone("second")

    runs = capturing_backend.runs
    assert len(runs) == 2
    assert runs[0]["trace_id"] != runs[1]["trace_id"]
    assert runs[0]["parent_id"] is None
    assert runs[1]["parent_id"] is None
