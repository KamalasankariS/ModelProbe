"""Unit tests for all five evaluators."""

from unittest.mock import MagicMock

import pytest

from modelprobe.evaluators.exact import ExactEvaluator
from modelprobe.evaluators.contains import ContainsEvaluator
from modelprobe.evaluators.regex import RegexEvaluator
from modelprobe.evaluators.json_schema import JsonSchemaEvaluator
from modelprobe.evaluators.llm_judge import LLMJudgeEvaluator
from modelprobe.evaluators import get_evaluator


class TestExactEvaluator:
    def test_pass_on_exact_match(self):
        ev = ExactEvaluator()
        r = ev.evaluate(output="hello", expected="hello")
        assert r["passed"] is True
        assert r["status"] == "pass"
        assert r["score"] == 1.0

    def test_fail_on_mismatch(self):
        ev = ExactEvaluator()
        r = ev.evaluate(output="hello", expected="world")
        assert r["passed"] is False
        assert r["status"] == "fail"
        assert r["score"] == 0.0

    def test_case_insensitive_mode(self):
        ev = ExactEvaluator()
        r = ev.evaluate(output="Hello", expected="hello", config={"case_sensitive": False})
        assert r["passed"] is True

    def test_no_expected_returns_error(self):
        ev = ExactEvaluator()
        r = ev.evaluate(output="anything")
        assert r["status"] == "error"


class TestContainsEvaluator:
    def test_any_mode_single_hit(self):
        ev = ContainsEvaluator()
        r = ev.evaluate(output="The total is $500", config={"values": ["$500", "$1000"]})
        assert r["passed"] is True
        assert r["status"] == "pass"

    def test_any_mode_no_hit(self):
        ev = ContainsEvaluator()
        r = ev.evaluate(output="nothing here", config={"values": ["$500", "$1000"]})
        assert r["passed"] is False
        assert r["status"] == "fail"

    def test_all_mode_partial_miss(self):
        ev = ContainsEvaluator()
        r = ev.evaluate(output="invoice total", config={"values": ["invoice", "$500"], "mode": "all"})
        assert r["passed"] is False
        assert r["score"] == 0.5

    def test_all_mode_all_present(self):
        ev = ContainsEvaluator()
        r = ev.evaluate(output="invoice total is $500", config={"values": ["invoice", "$500"], "mode": "all"})
        assert r["passed"] is True

    def test_missing_values_config_returns_error(self):
        ev = ContainsEvaluator()
        r = ev.evaluate(output="any", config={})
        assert r["status"] == "error"


class TestRegexEvaluator:
    def test_matching_pattern(self):
        ev = RegexEvaluator()
        r = ev.evaluate(output="Order #12345", config={"pattern": r"Order #\d+"})
        assert r["passed"] is True

    def test_non_matching_pattern(self):
        ev = RegexEvaluator()
        r = ev.evaluate(output="nothing", config={"pattern": r"\d{4}"})
        assert r["passed"] is False
        assert r["status"] == "fail"

    def test_invalid_pattern_returns_error(self):
        ev = RegexEvaluator()
        r = ev.evaluate(output="text", config={"pattern": "["})
        assert r["status"] == "error"

    def test_missing_pattern_returns_error(self):
        ev = RegexEvaluator()
        r = ev.evaluate(output="text", config={})
        assert r["status"] == "error"


class TestJsonSchemaEvaluator:
    def test_valid_json_matches_schema(self):
        ev = JsonSchemaEvaluator()
        r = ev.evaluate(
            output='{"name": "Alice", "age": 30}',
            config={"schema": {"type": "object", "required": ["name", "age"]}},
        )
        assert r["passed"] is True
        assert r["status"] == "pass"

    def test_schema_validation_failure(self):
        ev = JsonSchemaEvaluator()
        r = ev.evaluate(
            output='{"name": "Alice"}',
            config={"schema": {"type": "object", "required": ["name", "age"]}},
        )
        assert r["passed"] is False
        assert r["status"] == "fail"

    def test_invalid_json_returns_error_not_fail(self):
        ev = JsonSchemaEvaluator()
        r = ev.evaluate(output="not json at all", config={"schema": {"type": "object"}})
        assert r["status"] == "error"
        assert r["passed"] is False

    def test_missing_schema_config_returns_error(self):
        ev = JsonSchemaEvaluator()
        r = ev.evaluate(output="{}", config={})
        assert r["status"] == "error"


class TestLLMJudgeEvaluator:
    def test_timeout_produces_skipped(self, monkeypatch):
        import httpx

        def raise_timeout(*args, **kwargs):
            raise httpx.TimeoutException("timed out")

        monkeypatch.setattr(httpx, "post", raise_timeout)

        ev = LLMJudgeEvaluator()
        r = ev.evaluate(output="some output", config={"rubric": "Is it good?"})
        assert r["status"] == "skipped"
        assert "timed out" in r["reason"]
        assert r["passed"] is False

    def test_network_error_produces_skipped(self, monkeypatch):
        import httpx

        def raise_error(*args, **kwargs):
            raise httpx.ConnectError("connection refused")

        monkeypatch.setattr(httpx, "post", raise_error)

        ev = LLMJudgeEvaluator()
        r = ev.evaluate(output="some output", config={"rubric": "Is it correct?"})
        assert r["status"] == "skipped"
        assert r["passed"] is False

    def test_successful_pass_verdict(self, monkeypatch):
        import httpx

        mock_response = MagicMock()
        mock_response.raise_for_status = MagicMock()
        mock_response.json.return_value = {
            "choices": [{"message": {"content": '{"passed": true, "score": 0.95, "reason": "Correct"}'}}]
        }
        monkeypatch.setattr(httpx, "post", lambda *a, **k: mock_response)

        ev = LLMJudgeEvaluator()
        r = ev.evaluate(output="The capital is Paris.", config={"rubric": "Is the answer correct?"})
        assert r["passed"] is True
        assert r["status"] == "pass"
        assert r["score"] == 0.95

    def test_successful_fail_verdict(self, monkeypatch):
        import httpx

        mock_response = MagicMock()
        mock_response.raise_for_status = MagicMock()
        mock_response.json.return_value = {
            "choices": [{"message": {"content": '{"passed": false, "score": 0.1, "reason": "Wrong"}'}}]
        }
        monkeypatch.setattr(httpx, "post", lambda *a, **k: mock_response)

        ev = LLMJudgeEvaluator()
        r = ev.evaluate(output="Wrong answer.", config={"rubric": "Is it correct?"})
        assert r["passed"] is False
        assert r["status"] == "fail"

    def test_missing_rubric_produces_skipped(self):
        ev = LLMJudgeEvaluator()
        r = ev.evaluate(output="any", config={})
        assert r["status"] == "skipped"

    def test_empty_choices_produces_skipped(self, monkeypatch):
        import httpx

        mock_response = MagicMock()
        mock_response.raise_for_status = MagicMock()
        mock_response.json.return_value = {"choices": []}
        monkeypatch.setattr(httpx, "post", lambda *a, **k: mock_response)

        ev = LLMJudgeEvaluator()
        r = ev.evaluate(output="test", config={"rubric": "test"})
        assert r["status"] == "skipped"
        assert "missing" in r["reason"]

    def test_missing_passed_field_defaults_false(self, monkeypatch):
        import httpx

        mock_response = MagicMock()
        mock_response.raise_for_status = MagicMock()
        mock_response.json.return_value = {
            "choices": [{"message": {"content": '{"score": 0.3, "reason": "Partial"}'}}]
        }
        monkeypatch.setattr(httpx, "post", lambda *a, **k: mock_response)

        ev = LLMJudgeEvaluator()
        r = ev.evaluate(output="test", config={"rubric": "test"})
        assert r["passed"] is False


class TestGetEvaluator:
    def test_all_types_resolve(self):
        for name in ["exact", "contains", "regex", "json_schema", "llm_judge", "hallucination", "toxicity", "similarity"]:
            ev = get_evaluator(name)
            assert ev.name == name

    def test_unknown_type_raises(self):
        with pytest.raises(ValueError, match="Unknown eval_type"):
            get_evaluator("nonexistent")
