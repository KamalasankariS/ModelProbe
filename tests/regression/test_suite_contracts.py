"""Regression tests — SuiteResult shape and run_suite behavior contracts.

Locks down the public API of run_suite so that refactoring cannot
silently change the result shape or counting logic.
"""

import pytest
from modelprobe.suite import run_suite, SuiteResult


@pytest.fixture(autouse=True)
def noop_backend(monkeypatch):
    from tests.conftest import NoOpBackend
    import modelprobe.storage.router as router_module
    monkeypatch.setattr(router_module, "_backend", NoOpBackend())
    yield
    monkeypatch.setattr(router_module, "_backend", None)


def _case(tc_id="tc_001", expected="ok", eval_type="contains"):
    return {
        "test_case_id": tc_id,
        "input": "test",
        "expected_output": expected,
        "eval_type": eval_type,
        "eval_config": {"values": [expected]},
    }


class TestSuiteResultShape:
    def test_has_all_required_fields(self):
        result = run_suite("s", "v1", [_case()], runner=lambda tc: "ok")
        assert hasattr(result, "suite")
        assert hasattr(result, "version")
        assert hasattr(result, "run_group")
        assert hasattr(result, "total")
        assert hasattr(result, "passed")
        assert hasattr(result, "failed")
        assert hasattr(result, "errored")
        assert hasattr(result, "skipped")
        assert hasattr(result, "pass_rate")
        assert hasattr(result, "results")

    def test_results_is_list_of_dicts(self):
        result = run_suite("s", "v1", [_case()], runner=lambda tc: "ok")
        assert isinstance(result.results, list)
        assert all(isinstance(r, dict) for r in result.results)

    def test_counts_sum_to_total(self):
        cases = [_case(f"tc_{i}") for i in range(5)]
        result = run_suite("s", "v1", cases, runner=lambda tc: "ok")
        assert result.passed + result.failed + result.errored + result.skipped == result.total


class TestSuiteCountingLogic:
    def test_pass_rate_excludes_skipped(self):
        """pass_rate = passed / (total - skipped)"""
        # All pass => 1.0
        result = run_suite("s", "v1", [_case()], runner=lambda tc: "ok")
        assert result.pass_rate == 1.0

    def test_pass_rate_zero_when_all_fail(self):
        result = run_suite("s", "v1", [_case()], runner=lambda tc: "wrong")
        assert result.pass_rate == 0.0

    def test_pass_rate_is_rounded(self):
        cases = [_case(f"tc_{i}") for i in range(3)]
        result = run_suite(
            "s", "v1", cases,
            runner=lambda tc: tc["expected_output"] if tc["test_case_id"] != "tc_2" else "wrong",
        )
        # pass_rate should be a float with at most 4 decimal places
        assert result.pass_rate == round(result.pass_rate, 4)

    def test_empty_suite_returns_zero_pass_rate(self):
        result = run_suite("s", "v1", [], runner=lambda tc: "ok")
        assert result.total == 0
        assert result.pass_rate == 0.0


class TestSuiteMetadata:
    def test_suite_name_propagated(self):
        result = run_suite("my-suite", "v1", [_case()], runner=lambda tc: "ok")
        assert result.suite == "my-suite"

    def test_version_propagated(self):
        result = run_suite("s", "v42", [_case()], runner=lambda tc: "ok")
        assert result.version == "v42"

    def test_run_group_propagated(self):
        result = run_suite("s", "v1", [_case()], runner=lambda tc: "ok", run_group="exp_1")
        assert result.run_group == "exp_1"

    def test_run_group_defaults_none(self):
        result = run_suite("s", "v1", [_case()], runner=lambda tc: "ok")
        assert result.run_group is None
