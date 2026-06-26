"""Unit tests for the toxicity evaluator."""

import pytest

from modelprobe.evaluators.toxicity import ToxicityEvaluator


@pytest.fixture
def ev():
    return ToxicityEvaluator()


class TestCleanText:

    def test_clean_text_passes(self, ev):
        r = ev.evaluate(output="Thank you for your patience. Let me help you.")
        assert r["passed"] is True
        assert r["status"] == "pass"
        assert r["score"] == 1.0

    def test_clean_text_detail_has_categories(self, ev):
        r = ev.evaluate(output="Hello, how can I help?")
        assert "categories_checked" in r["detail"]
        assert len(r["detail"]["categories_checked"]) > 0
        assert r["detail"]["detections"] == {}

    def test_empty_string_passes(self, ev):
        r = ev.evaluate(output="")
        assert r["passed"] is True
        assert r["score"] == 1.0


class TestProfanityDetection:

    def test_profanity_detected(self, ev):
        r = ev.evaluate(output="What the fuck is going on")
        assert r["passed"] is False
        assert r["status"] == "fail"
        assert r["score"] < 1.0
        assert "profanity" in r["detail"]["detections"]

    def test_profanity_with_threshold_allows_some(self, ev):
        r = ev.evaluate(
            output="That damn thing broke again",
            config={"threshold": 0.5},
        )
        # "damn" is 1 hit in 5 words = 0.2 toxicity ratio, score = 0.8
        # threshold 0.5 means pass if score >= 0.5
        assert r["passed"] is True


class TestPIIDetection:

    def test_ssn_detected(self, ev):
        r = ev.evaluate(
            output="Your SSN is 123-45-6789",
            config={"categories": ["pii"]},
        )
        assert r["passed"] is False
        assert "pii" in r["detail"]["detections"]

    def test_email_detected(self, ev):
        r = ev.evaluate(
            output="Contact me at john@example.com",
            config={"categories": ["pii"]},
        )
        assert r["passed"] is False
        assert "pii" in r["detail"]["detections"]

    def test_credit_card_detected(self, ev):
        r = ev.evaluate(
            output="Card number is 4111 1111 1111 1111",
            config={"categories": ["pii"]},
        )
        assert r["passed"] is False
        assert "pii" in r["detail"]["detections"]

    def test_phone_detected(self, ev):
        r = ev.evaluate(
            output="Call me at (555) 123-4567",
            config={"categories": ["pii"]},
        )
        assert r["passed"] is False
        assert "pii" in r["detail"]["detections"]


class TestCategoryFiltering:

    def test_only_checks_specified_categories(self, ev):
        # Text has profanity but we only check for pii
        r = ev.evaluate(
            output="What the fuck",
            config={"categories": ["pii"]},
        )
        assert r["passed"] is True
        assert r["score"] == 1.0

    def test_unknown_category_is_harmless(self, ev):
        r = ev.evaluate(
            output="Hello world",
            config={"categories": ["nonexistent_category"]},
        )
        assert r["passed"] is True


class TestViolenceDetection:

    def test_violence_detected(self, ev):
        r = ev.evaluate(
            output="I will kill you",
            config={"categories": ["violence"]},
        )
        assert r["passed"] is False
        assert "violence" in r["detail"]["detections"]


class TestSelfHarmDetection:

    def test_self_harm_detected(self, ev):
        r = ev.evaluate(
            output="You should kill yourself",
            config={"categories": ["self_harm"]},
        )
        assert r["passed"] is False
        assert "self_harm" in r["detail"]["detections"]


class TestEvaluatorMeta:

    def test_evaluator_name(self, ev):
        assert ev.name == "toxicity"

    def test_result_has_evaluator_field(self, ev):
        r = ev.evaluate(output="clean text")
        assert r["evaluator"] == "toxicity"

    def test_total_hits_in_detail(self, ev):
        r = ev.evaluate(output="fuck shit damn")
        assert r["detail"]["total_hits"] >= 3
