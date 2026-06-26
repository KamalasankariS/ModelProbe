"""Unit tests for the similarity evaluator."""

import pytest

from modelprobe.evaluators.similarity import SimilarityEvaluator


@pytest.fixture
def ev():
    return SimilarityEvaluator()


class TestTFIDF:

    def test_identical_strings_score_1(self, ev):
        r = ev.evaluate(
            output="The capital of France is Paris",
            expected="The capital of France is Paris",
            config={"strategy": "tfidf", "threshold": 0.7},
        )
        assert r["passed"] is True
        assert r["score"] == 1.0
        assert r["status"] == "pass"

    def test_similar_strings_pass(self, ev):
        r = ev.evaluate(
            output="Paris is the capital city of France",
            expected="The capital of France is Paris",
            config={"strategy": "tfidf", "threshold": 0.5},
        )
        assert r["passed"] is True
        assert r["score"] > 0.5

    def test_unrelated_strings_fail(self, ev):
        r = ev.evaluate(
            output="The weather is sunny today",
            expected="Quantum computing uses qubits",
            config={"strategy": "tfidf", "threshold": 0.5},
        )
        assert r["passed"] is False
        assert r["score"] < 0.5

    def test_default_strategy_is_tfidf(self, ev):
        r = ev.evaluate(
            output="hello world",
            expected="hello world",
        )
        assert r["passed"] is True
        assert r["detail"]["strategy"] == "tfidf"


class TestJaccard:

    def test_identical_strings(self, ev):
        r = ev.evaluate(
            output="the quick brown fox",
            expected="the quick brown fox",
            config={"strategy": "jaccard", "threshold": 0.7},
        )
        assert r["score"] == 1.0
        assert r["passed"] is True

    def test_partial_overlap(self, ev):
        r = ev.evaluate(
            output="the quick brown fox",
            expected="the slow brown dog",
            config={"strategy": "jaccard", "threshold": 0.3},
        )
        # overlap: {the, brown} / union: {the, quick, brown, fox, slow, dog} = 2/6
        assert r["score"] == pytest.approx(2 / 6, abs=0.01)

    def test_no_overlap_fails(self, ev):
        r = ev.evaluate(
            output="hello world",
            expected="foo bar",
            config={"strategy": "jaccard", "threshold": 0.1},
        )
        assert r["passed"] is False
        assert r["score"] == 0.0


class TestNgram:

    def test_identical_strings(self, ev):
        r = ev.evaluate(
            output="the quick brown fox jumps",
            expected="the quick brown fox jumps",
            config={"strategy": "ngram", "threshold": 0.7, "n": 2},
        )
        assert r["score"] == 1.0
        assert r["passed"] is True

    def test_partial_ngram_overlap(self, ev):
        r = ev.evaluate(
            output="the quick brown fox jumps over",
            expected="the quick brown dog runs over",
            config={"strategy": "ngram", "threshold": 0.3, "n": 2},
        )
        assert r["score"] > 0.0
        assert r["score"] < 1.0

    def test_custom_n_value(self, ev):
        r = ev.evaluate(
            output="a b c d e",
            expected="a b c d e",
            config={"strategy": "ngram", "n": 3, "threshold": 0.5},
        )
        assert r["score"] == 1.0


class TestEdgeCases:

    def test_missing_expected_returns_error(self, ev):
        r = ev.evaluate(output="some text")
        assert r["status"] == "error"
        assert r["passed"] is False

    def test_empty_expected_returns_error(self, ev):
        r = ev.evaluate(output="some text", expected="")
        assert r["status"] == "error"

    def test_empty_output_scores_zero(self, ev):
        r = ev.evaluate(output="", expected="hello world")
        assert r["score"] == 0.0

    def test_unknown_strategy_returns_error(self, ev):
        r = ev.evaluate(
            output="text",
            expected="text",
            config={"strategy": "nonexistent"},
        )
        assert r["status"] == "error"

    def test_threshold_boundary(self, ev):
        # Score exactly at threshold should pass
        r = ev.evaluate(
            output="hello world",
            expected="hello world",
            config={"threshold": 1.0},
        )
        assert r["passed"] is True


class TestEvaluatorMeta:

    def test_evaluator_name(self, ev):
        assert ev.name == "similarity"

    def test_result_has_detail(self, ev):
        r = ev.evaluate(output="hello", expected="hello")
        assert "strategy" in r["detail"]
        assert "threshold" in r["detail"]

    def test_result_has_evaluator_field(self, ev):
        r = ev.evaluate(output="hello", expected="hello")
        assert r["evaluator"] == "similarity"
