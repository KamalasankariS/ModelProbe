"""Evaluator return shape contracts."""

import pytest
from modelprobe.evaluators import get_evaluator

REQUIRED_KEYS = {"passed", "score", "reason", "status", "evaluator"}
VALID_STATUSES = {"pass", "fail", "error", "skipped"}


@pytest.mark.parametrize("eval_type,output,expected,config", [
    ("exact", "hello", "hello", {}),
    ("exact", "hello", "world", {}),
    ("exact", "hello", None, {}),
    ("contains", "The total is $500", None, {"values": ["$500"]}),
    ("contains", "nothing", None, {"values": ["$500"]}),
    ("contains", "text", None, {}),
    ("regex", "Order #12345", None, {"pattern": r"Order #\d+"}),
    ("regex", "nothing", None, {"pattern": r"\d{4}"}),
    ("regex", "text", None, {}),
    ("json_schema", '{"name": "Alice"}', None, {"schema": {"type": "object", "required": ["name"]}}),
    ("json_schema", "not json", None, {"schema": {"type": "object"}}),
    ("json_schema", "{}", None, {}),
])
def test_evaluator_returns_required_keys(eval_type, output, expected, config):
    ev = get_evaluator(eval_type)
    result = ev.evaluate(output=output, expected=expected, config=config)
    assert REQUIRED_KEYS.issubset(result.keys()), f"Missing keys: {REQUIRED_KEYS - result.keys()}"


@pytest.mark.parametrize("eval_type,output,expected,config", [
    ("exact", "hello", "hello", {}),
    ("contains", "abc", None, {"values": ["abc"]}),
    ("regex", "123", None, {"pattern": r"\d+"}),
    ("json_schema", '{"a": 1}', None, {"schema": {"type": "object"}}),
])
def test_passing_evaluator_has_correct_status_and_score(eval_type, output, expected, config):
    ev = get_evaluator(eval_type)
    result = ev.evaluate(output=output, expected=expected, config=config)
    assert result["passed"] is True
    assert result["status"] == "pass"
    assert result["score"] > 0


@pytest.mark.parametrize("eval_type,output,expected,config", [
    ("exact", "hello", "world", {}),
    ("contains", "nothing", None, {"values": ["xyz"]}),
    ("regex", "abc", None, {"pattern": r"\d+"}),
    ("json_schema", '{"name": "Alice"}', None, {"schema": {"type": "object", "required": ["age"]}}),
])
def test_failing_evaluator_has_correct_status_and_score(eval_type, output, expected, config):
    ev = get_evaluator(eval_type)
    result = ev.evaluate(output=output, expected=expected, config=config)
    assert result["passed"] is False
    assert result["status"] in ("fail", "error")


def test_score_is_always_numeric():
    for eval_type in ["exact", "contains", "regex", "json_schema"]:
        ev = get_evaluator(eval_type)
        result = ev.evaluate(output="test", expected="test", config={
            "values": ["test"], "pattern": "test", "schema": {"type": "string"}
        })
        assert isinstance(result["score"], (int, float))


def test_status_is_always_valid():
    for eval_type in ["exact", "contains", "regex", "json_schema"]:
        ev = get_evaluator(eval_type)
        result = ev.evaluate(output="test", expected="test", config={
            "values": ["test"], "pattern": "test", "schema": {"type": "string"}
        })
        assert result["status"] in VALID_STATUSES, f"Invalid status: {result['status']}"


def test_evaluator_name_matches_registry_key():
    for name in ["exact", "contains", "regex", "json_schema", "llm_judge"]:
        ev = get_evaluator(name)
        assert ev.name == name
