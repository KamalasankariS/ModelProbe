"""Tests for run_suite and assert_eval."""

import pytest
from modelprobe.suite import run_suite, assert_eval, SuiteResult


class _NoOpBackend:
    def write_run(self, run): pass
    def get_run(self, run_id): return None
    def list_runs(self, filters=None): return []
    def write_eval_result(self, result): pass
    def write_test_case(self, tc): pass
    def list_test_cases(self, suite): return []
    def list_eval_results(self, run_id): return []
    def list_suites(self): return []


@pytest.fixture(autouse=True)
def patch_backend(monkeypatch):
    import modelprobe.storage.router as router_module
    monkeypatch.setattr(router_module, "_backend", _NoOpBackend())
    yield
    monkeypatch.setattr(router_module, "_backend", None)


def _make_test_case(tc_id, expected, eval_type="contains", values=None):
    return {
        "test_case_id": tc_id,
        "input": "input text",
        "expected_output": expected,
        "eval_type": eval_type,
        "eval_config": {"values": values or [expected]},
    }


def test_all_pass(patch_backend):
    cases = [_make_test_case("tc_001", "correct")]
    result = run_suite(
        suite_name="test",
        version="v1",
        test_cases=cases,
        runner=lambda tc: "this is correct",
    )
    assert isinstance(result, SuiteResult)
    assert result.passed == 1
    assert result.failed == 0
    assert result.errored == 0
    assert result.skipped == 0
    assert result.total == 1
    assert result.pass_rate == 1.0


def test_all_fail(patch_backend):
    cases = [_make_test_case("tc_001", "expected")]
    result = run_suite(
        suite_name="test",
        version="v1",
        test_cases=cases,
        runner=lambda tc: "completely wrong",
    )
    assert result.failed == 1
    assert result.passed == 0
    assert result.pass_rate == 0.0


def test_mixed_results(patch_backend):
    cases = [
        _make_test_case("tc_001", "apple"),
        _make_test_case("tc_002", "banana"),
        _make_test_case("tc_003", "cherry"),
    ]
    result = run_suite(
        suite_name="test",
        version="v1",
        test_cases=cases,
        runner=lambda tc: tc["expected_output"] if tc["test_case_id"] != "tc_002" else "wrong",
    )
    assert result.total == 3
    assert result.passed == 2
    assert result.failed == 1
    assert round(result.pass_rate, 4) == round(2 / 3, 4)


def test_runner_exception_counts_as_error(patch_backend):
    cases = [_make_test_case("tc_001", "anything")]
    result = run_suite(
        suite_name="test",
        version="v1",
        test_cases=cases,
        runner=lambda tc: (_ for _ in ()).throw(RuntimeError("boom")),
    )
    assert result.errored == 1
    assert result.passed == 0
    assert result.pass_rate == 0.0


def test_suite_result_shape(patch_backend):
    result = run_suite(
        suite_name="my-suite",
        version="v3",
        test_cases=[_make_test_case("tc_001", "ok")],
        runner=lambda tc: "ok",
        run_group="experiment_1",
    )
    assert result.suite == "my-suite"
    assert result.version == "v3"
    assert result.run_group == "experiment_1"
    assert isinstance(result.results, list)
    assert len(result.results) == 1


def test_assert_eval_passes_silently():
    result = assert_eval("hello world", "contains", {"values": ["hello"]})
    assert result["passed"] is True


def test_assert_eval_raises_on_failure():
    with pytest.raises(AssertionError):
        assert_eval("goodbye world", "contains", {"values": ["hello"]})


def test_assert_eval_skipped_does_not_raise():
    from modelprobe.evaluators.llm_judge import LLMJudgeEvaluator
    import modelprobe.evaluators as ev_module

    class AlwaysSkip(LLMJudgeEvaluator):
        def evaluate(self, output, expected=None, config=None):
            return self._skipped("forced skip")

    original = ev_module._REGISTRY["llm_judge"]
    ev_module._REGISTRY["llm_judge"] = AlwaysSkip
    try:
        result = assert_eval("output", "llm_judge", {"rubric": "test"})
        assert result["status"] == "skipped"
    finally:
        ev_module._REGISTRY["llm_judge"] = original
