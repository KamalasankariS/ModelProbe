"""Unit tests for the hallucination evaluator."""

from unittest.mock import MagicMock, patch

import pytest

from modelprobe.evaluators.hallucination import HallucinationEvaluator


@pytest.fixture
def ev():
    return HallucinationEvaluator()


# -- consistency strategy ------------------------------------------------------


class TestConsistency:

    def test_high_agreement_passes(self, ev):
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.raise_for_status = MagicMock()
        mock_resp.json.return_value = {"response": "The capital of France is Paris."}

        with patch("httpx.post", return_value=mock_resp):
            result = ev.evaluate(
                output="The capital of France is Paris.",
                config={
                    "strategy": "consistency",
                    "prompt": "What is the capital of France?",
                    "model": "llama3",
                    "endpoint": "http://localhost:11434/api/generate",
                    "samples": 3,
                    "threshold": 0.5,
                },
            )
        assert result["passed"] is True
        assert result["status"] == "pass"
        assert result["score"] == 1.0

    def test_low_agreement_fails(self, ev):
        responses = iter([
            {"response": "The capital is Lyon."},
            {"response": "It's Marseille, obviously."},
            {"response": "Berlin is the capital."},
        ])

        def side_effect(*args, **kwargs):
            mock = MagicMock()
            mock.raise_for_status = MagicMock()
            mock.json.return_value = next(responses)
            return mock

        with patch("httpx.post", side_effect=side_effect):
            result = ev.evaluate(
                output="The capital of France is Paris.",
                config={
                    "strategy": "consistency",
                    "prompt": "What is the capital of France?",
                    "model": "llama3",
                    "samples": 3,
                    "threshold": 0.5,
                },
            )
        assert result["passed"] is False
        assert result["status"] == "fail"
        assert result["score"] < 0.5

    def test_connection_error_returns_error(self, ev):
        with patch("httpx.post", side_effect=ConnectionError("refused")):
            result = ev.evaluate(
                output="anything",
                config={
                    "strategy": "consistency",
                    "prompt": "test",
                    "model": "llama3",
                    "samples": 3,
                },
            )
        assert result["status"] == "error"
        assert "0 response" in result["reason"] or "1 response" in result["reason"]

    def test_missing_prompt_returns_error(self, ev):
        result = ev.evaluate(
            output="test",
            config={"strategy": "consistency", "model": "llama3"},
        )
        assert result["status"] == "error"
        assert "prompt" in result["reason"]

    def test_missing_model_returns_error(self, ev):
        result = ev.evaluate(
            output="test",
            config={"strategy": "consistency", "prompt": "What is 2+2?"},
        )
        assert result["status"] == "error"
        assert "model" in result["reason"]


# -- factual strategy ----------------------------------------------------------


class TestFactual:

    def _wiki_entity_response(self, entity_id, prop, value_id):
        return {
            "entities": {
                entity_id: {
                    "claims": {
                        prop: [{
                            "mainsnak": {
                                "datavalue": {
                                    "type": "wikibase-entityid",
                                    "value": {"id": value_id},
                                }
                            }
                        }]
                    }
                }
            }
        }

    def _label_response(self, entity_id, label):
        return {
            "entities": {
                entity_id: {
                    "labels": {"en": {"value": label}}
                }
            }
        }

    @patch("time.sleep")
    def test_verified_claim_passes(self, _sleep, ev):
        def mock_get(url, **kwargs):
            mock = MagicMock()
            mock.raise_for_status = MagicMock()
            if "Q142" in url:
                mock.json.return_value = self._wiki_entity_response("Q142", "P36", "Q90")
            elif "Q90" in url:
                mock.json.return_value = self._label_response("Q90", "Paris")
            return mock

        with patch("httpx.get", side_effect=mock_get):
            result = ev.evaluate(
                output="The capital of France is Paris.",
                config={
                    "strategy": "factual",
                    "claims": [
                        {"subject": "Q142", "property": "P36", "expected_label": "Paris"}
                    ],
                },
            )
        assert result["passed"] is True
        assert result["status"] == "pass"
        assert result["score"] == 1.0

    @patch("time.sleep")
    def test_contradicted_claim_fails(self, _sleep, ev):
        def mock_get(url, **kwargs):
            mock = MagicMock()
            mock.raise_for_status = MagicMock()
            if "Q142" in url:
                mock.json.return_value = self._wiki_entity_response("Q142", "P36", "Q90")
            elif "Q90" in url:
                mock.json.return_value = self._label_response("Q90", "Paris")
            return mock

        with patch("httpx.get", side_effect=mock_get):
            result = ev.evaluate(
                output="The capital of France is Lyon.",
                config={
                    "strategy": "factual",
                    "claims": [
                        {"subject": "Q142", "property": "P36", "expected_label": "Lyon"}
                    ],
                },
            )
        assert result["passed"] is False
        assert result["status"] == "fail"

    @patch("time.sleep")
    def test_wikidata_error_returns_unresolved(self, _sleep, ev):
        with patch("httpx.get", side_effect=Exception("timeout")):
            result = ev.evaluate(
                output="The capital of France is Paris.",
                config={
                    "strategy": "factual",
                    "claims": [
                        {"subject": "Q142", "property": "P36", "expected_label": "Paris"}
                    ],
                },
            )
        assert result["status"] == "skipped"
        assert "unresolved" in result["reason"]

    def test_missing_claims_returns_error(self, ev):
        result = ev.evaluate(
            output="test",
            config={"strategy": "factual"},
        )
        assert result["status"] == "error"
        assert "claims" in result["reason"]


# -- invalid strategy ----------------------------------------------------------


class TestInvalidStrategy:

    def test_unknown_strategy(self, ev):
        result = ev.evaluate(
            output="test",
            config={"strategy": "quantum_entanglement"},
        )
        assert result["status"] == "error"
        assert "Unknown strategy" in result["reason"]


# -- helper methods ------------------------------------------------------------


class TestHelpers:

    def test_extract_key_tokens_numbers(self, ev):
        tokens = ev._extract_key_tokens("The answer is 42 or 3.14")
        assert "42" in tokens
        assert "3.14" in tokens

    def test_extract_key_tokens_capitalized(self, ev):
        tokens = ev._extract_key_tokens("Paris and London are cities")
        assert "paris" in tokens
        assert "london" in tokens

    def test_extract_key_tokens_booleans(self, ev):
        tokens = ev._extract_key_tokens("The result is True and none")
        assert "true" in tokens
        assert "none" in tokens

    def test_agreement_identical(self, ev):
        score = ev._agreement_score("Paris is great", ["Paris is great", "Paris is great"])
        assert score == 1.0

    def test_agreement_completely_different(self, ev):
        score = ev._agreement_score("Paris is great", ["Berlin rocks", "Tokyo wins"])
        assert score < 0.5

    def test_jaccard_avg_empty(self, ev):
        score = ev._jaccard_avg("", ["hello"])
        assert score == 0.0

    def test_error_helper(self, ev):
        result = ev._error("something broke")
        assert result["passed"] is False
        assert result["score"] == 0.0
        assert result["status"] == "error"
        assert result["reason"] == "something broke"
