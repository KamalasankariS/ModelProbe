"""ModelProbe test suite runner.

Usage::

    from modelprobe import run_suite, assert_eval

    test_cases = [
        {
            "test_case_id": "tc_001",
            "input": "What is 2+2?",
            "expected_output": "4",
            "eval_type": "contains",
            "eval_config": {"values": ["4"]},
        }
    ]

    result = run_suite(
        suite_name="math-agent",
        version="v1",
        test_cases=test_cases,
        runner=lambda tc: my_model(tc["input"]),
    )
    print(result.pass_rate)
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional
from uuid import uuid4

log = logging.getLogger(__name__)


@dataclass
class SuiteResult:
    """Aggregated result of a test suite run.

    Attributes:
        suite:      Suite name.
        version:    Version string.
        run_group:  Optional experiment label.
        total:      Total test cases executed.
        passed:     Cases with status "pass".
        failed:     Cases with status "fail".
        errored:    Cases with status "error".
        skipped:    Cases with status "skipped".
        pass_rate:  passed / (total - skipped), or 0.0 if no scoreable cases.
        results:    List of individual EvalResult dicts.
    """

    suite: str
    version: str
    run_group: Optional[str]
    total: int
    passed: int
    failed: int
    errored: int
    skipped: int
    pass_rate: float
    results: List[Dict[str, Any]] = field(default_factory=list)


def run_suite(
    suite_name: str,
    version: str,
    test_cases: List[Dict[str, Any]],
    runner: Callable[[Dict[str, Any]], str],
    run_group: Optional[str] = None,
    tags: Optional[Dict[str, str]] = None,
    commit_hash: Optional[str] = None,
) -> SuiteResult:
    """Run a list of test cases through a callable and evaluate each output.

    Args:
        suite_name:  Suite identifier.
        version:     Deployment version string.
        test_cases:  List of test case dicts with keys: test_case_id, input,
                     expected_output, eval_type, eval_config.
        runner:      Callable that accepts a test case dict and returns a str.
        run_group:   Optional experiment label.
        tags:        Arbitrary key-value metadata attached to every run.
        commit_hash: Optional git commit SHA.

    Returns:
        A SuiteResult with pass/fail/error/skipped counts and per-case results.

    Usage::

        result = run_suite(
            suite_name="invoice-agent",
            version="v2",
            test_cases=[...],
            runner=lambda tc: my_model(tc["input"]),
        )
        print(f"Pass rate: {result.pass_rate:.1%}")
    """
    from modelprobe.evaluators import get_evaluator
    from modelprobe.storage import router

    _tags = tags or {}
    results: List[Dict[str, Any]] = []
    passed = failed = errored = skipped = 0

    for tc in test_cases:
        tc_id = tc.get("test_case_id", str(uuid4()))
        eval_type = tc.get("eval_type", "exact")
        eval_config = tc.get("eval_config", {})
        expected = tc.get("expected_output")
        run_id = str(uuid4())

        try:
            output = str(runner(tc))
        except Exception as exc:
            output = f"{type(exc).__name__}: {exc}"
            result = {
                "id": str(uuid4()),
                "run_id": run_id,
                "test_case_id": tc_id,
                "passed": False,
                "score": 0.0,
                "reason": f"Runner raised an exception: {output}",
                "status": "error",
                "evaluator": eval_type,
            }
            errored += 1
            results.append(result)
            router.write_eval_result(result)
            continue

        try:
            evaluator = get_evaluator(eval_type)
            result = evaluator.evaluate(output=output, expected=expected, config=eval_config)
        except Exception as exc:
            result = {
                "id": str(uuid4()),
                "run_id": run_id,
                "test_case_id": tc_id,
                "passed": False,
                "score": 0.0,
                "reason": f"Evaluator error: {exc}",
                "status": "error",
                "evaluator": eval_type,
            }
            errored += 1
            results.append(result)
            router.write_eval_result(result)
            continue

        result["id"] = result.get("id", str(uuid4()))
        result["run_id"] = run_id
        result["test_case_id"] = tc_id

        status = result.get("status", "fail")
        if status == "pass":
            passed += 1
        elif status == "fail":
            failed += 1
        elif status == "error":
            errored += 1
        elif status == "skipped":
            skipped += 1

        results.append(result)

        router.write_eval_result(result)

        router.write_run({
            "id": run_id,
            "trace_id": run_id,
            "parent_id": None,
            "suite": suite_name,
            "version": version,
            "run_group": run_group,
            "commit_hash": commit_hash,
            "tags": _tags,
            "input": tc.get("input"),
            "output": output,
            "status": status,
            "latency_ms": None,
            "token_count": None,
        })

    total = len(test_cases)
    scoreable = total - skipped
    pass_rate = passed / scoreable if scoreable > 0 else 0.0

    return SuiteResult(
        suite=suite_name,
        version=version,
        run_group=run_group,
        total=total,
        passed=passed,
        failed=failed,
        errored=errored,
        skipped=skipped,
        pass_rate=round(pass_rate, 4),
        results=results,
    )


def assert_eval(
    output: str,
    eval_type: str,
    config: Optional[Dict[str, Any]] = None,
    expected: Optional[str] = None,
) -> Dict[str, Any]:
    """Evaluate a single output inline and return the EvalResult dict.

    Raises:
        AssertionError: If the evaluation does not pass.

    Usage::

        from modelprobe import assert_eval
        assert_eval("hello world", "contains", {"values": ["hello"]})
    """
    from modelprobe.evaluators import get_evaluator

    evaluator = get_evaluator(eval_type)
    result = evaluator.evaluate(output=output, expected=expected, config=config or {})

    if not result["passed"] and result["status"] not in ("skipped", "error"):
        raise AssertionError(
            f"Eval '{eval_type}' failed: {result.get('reason', 'no reason')}"
        )

    return result
