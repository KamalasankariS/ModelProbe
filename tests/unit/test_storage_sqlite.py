"""Unit tests for the SQLite storage backend."""

import tempfile
import os
import pytest

from modelprobe.storage.sqlite import SQLiteBackend


@pytest.fixture
def backend():
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        db_path = f.name
    b = SQLiteBackend(db_path)
    yield b
    os.unlink(db_path)


def _make_run(run_id="r1", suite="test-suite", version="v1", **kwargs):
    base = {
        "id": run_id,
        "trace_id": kwargs.get("trace_id", "t1"),
        "parent_id": kwargs.get("parent_id"),
        "suite": suite,
        "version": version,
        "run_group": kwargs.get("run_group"),
        "commit_hash": kwargs.get("commit_hash"),
        "tags": kwargs.get("tags", {}),
        "input": kwargs.get("input", "test input"),
        "output": kwargs.get("output", "test output"),
        "status": kwargs.get("status", "pass"),
        "latency_ms": kwargs.get("latency_ms"),
        "token_count": kwargs.get("token_count"),
    }
    return base


class TestWriteAndGetRun:
    def test_write_and_read_back(self, backend):
        run = _make_run()
        backend.write_run(run)
        result = backend.get_run("r1")
        assert result is not None
        assert result["id"] == "r1"
        assert result["suite"] == "test-suite"
        assert result["status"] == "pass"

    def test_get_nonexistent_run(self, backend):
        assert backend.get_run("nonexistent") is None

    def test_tags_are_persisted(self, backend):
        run = _make_run(tags={"env": "staging", "team": "ml"})
        backend.write_run(run)
        result = backend.get_run("r1")
        assert result["tags"] == {"env": "staging", "team": "ml"}

    def test_upsert_on_duplicate_id(self, backend):
        backend.write_run(_make_run(status="pass"))
        backend.write_run(_make_run(status="fail"))
        result = backend.get_run("r1")
        assert result["status"] == "fail"


class TestListRuns:
    def test_filter_by_suite(self, backend):
        backend.write_run(_make_run(run_id="r1", suite="a"))
        backend.write_run(_make_run(run_id="r2", suite="b"))
        results = backend.list_runs({"suite": "a"})
        assert len(results) == 1
        assert results[0]["suite"] == "a"

    def test_filter_by_version(self, backend):
        backend.write_run(_make_run(run_id="r1", version="v1"))
        backend.write_run(_make_run(run_id="r2", version="v2"))
        results = backend.list_runs({"version": "v2"})
        assert len(results) == 1
        assert results[0]["version"] == "v2"

    def test_filter_by_status(self, backend):
        backend.write_run(_make_run(run_id="r1", status="pass"))
        backend.write_run(_make_run(run_id="r2", status="fail"))
        results = backend.list_runs({"status": "fail"})
        assert len(results) == 1
        assert results[0]["status"] == "fail"

    def test_filter_by_tag(self, backend):
        backend.write_run(_make_run(run_id="r1", tags={"env": "prod"}))
        backend.write_run(_make_run(run_id="r2", tags={"env": "staging"}))
        results = backend.list_runs({"tag": "env:prod"})
        assert len(results) == 1
        assert results[0]["tags"]["env"] == "prod"

    def test_empty_results(self, backend):
        results = backend.list_runs({"suite": "nonexistent"})
        assert results == []


class TestEvalResults:
    def test_write_and_list_eval_results(self, backend):
        backend.write_run(_make_run())
        backend.write_eval_result({
            "id": "e1",
            "run_id": "r1",
            "test_case_id": "tc_001",
            "passed": True,
            "score": 1.0,
            "reason": "Exact match",
            "status": "pass",
            "evaluator": "exact",
        })
        results = backend.list_eval_results("r1")
        assert len(results) == 1
        assert results[0]["passed"] is True
        assert results[0]["evaluator"] == "exact"


class TestTestCases:
    def test_write_and_list_test_cases(self, backend):
        backend.write_test_case({
            "id": "tc1",
            "suite": "my-suite",
            "test_case_id": "tc_001",
            "input": "What is 2+2?",
            "expected_output": "4",
            "eval_type": "exact",
            "eval_config": {},
        })
        cases = backend.list_test_cases("my-suite")
        assert len(cases) == 1
        assert cases[0]["test_case_id"] == "tc_001"


class TestListSuites:
    def test_distinct_suites(self, backend):
        backend.write_run(_make_run(run_id="r1", suite="alpha"))
        backend.write_run(_make_run(run_id="r2", suite="beta"))
        backend.write_run(_make_run(run_id="r3", suite="alpha"))
        suites = backend.list_suites()
        assert set(suites) == {"alpha", "beta"}
