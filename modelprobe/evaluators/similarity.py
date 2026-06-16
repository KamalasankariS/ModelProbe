"""Semantic similarity evaluator.

Compares the meaning of model output to expected output using token-level
similarity metrics. Works entirely offline — no embeddings API needed.

Strategies:
    - tfidf: TF-IDF cosine similarity (default, zero dependencies)
    - jaccard: Token-level Jaccard similarity
    - ngram: N-gram overlap (BLEU-like)

Config::

    {
        "strategy": "tfidf",
        "threshold": 0.7
    }
"""

from __future__ import annotations

import math
import re
from collections import Counter
from typing import Any, Dict, Optional


class SimilarityEvaluator:

    name = "similarity"

    def evaluate(
        self,
        output: str,
        expected: Optional[str] = None,
        config: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        config = config or {}
        strategy = config.get("strategy", "tfidf")
        threshold = float(config.get("threshold", 0.7))

        if not expected:
            return self._error("similarity evaluator requires 'expected' output")

        if strategy == "tfidf":
            score = self._tfidf_cosine(output, expected)
        elif strategy == "jaccard":
            score = self._jaccard(output, expected)
        elif strategy == "ngram":
            n = int(config.get("n", 2))
            score = self._ngram_overlap(output, expected, n)
        else:
            return self._error(f"Unknown strategy '{strategy}'")

        passed = score >= threshold
        return {
            "passed": passed,
            "score": round(score, 4),
            "reason": f"{strategy} similarity: {score:.2%} (threshold: {threshold:.0%})",
            "status": "pass" if passed else "fail",
            "evaluator": self.name,
            "detail": {"strategy": strategy, "threshold": threshold},
        }

    def _tokenize(self, text: str) -> list[str]:
        return re.findall(r'\b\w+\b', text.lower())

    def _tfidf_cosine(self, a: str, b: str) -> float:
        tokens_a = self._tokenize(a)
        tokens_b = self._tokenize(b)
        if not tokens_a or not tokens_b:
            return 0.0

        tf_a = Counter(tokens_a)
        tf_b = Counter(tokens_b)
        all_terms = set(tf_a.keys()) | set(tf_b.keys())

        # IDF based on these two "documents"
        doc_count = {}
        for t in all_terms:
            doc_count[t] = (1 if t in tf_a else 0) + (1 if t in tf_b else 0)

        def tfidf_vec(tf: Counter) -> Dict[str, float]:
            return {t: tf.get(t, 0) * math.log(2 / doc_count[t] + 1) for t in all_terms}

        vec_a = tfidf_vec(tf_a)
        vec_b = tfidf_vec(tf_b)

        dot = sum(vec_a[t] * vec_b[t] for t in all_terms)
        mag_a = math.sqrt(sum(v ** 2 for v in vec_a.values()))
        mag_b = math.sqrt(sum(v ** 2 for v in vec_b.values()))

        if mag_a == 0 or mag_b == 0:
            return 0.0
        return dot / (mag_a * mag_b)

    def _jaccard(self, a: str, b: str) -> float:
        set_a = set(self._tokenize(a))
        set_b = set(self._tokenize(b))
        if not set_a and not set_b:
            return 1.0
        union = set_a | set_b
        if not union:
            return 0.0
        return len(set_a & set_b) / len(union)

    def _ngram_overlap(self, a: str, b: str, n: int = 2) -> float:
        tokens_a = self._tokenize(a)
        tokens_b = self._tokenize(b)

        def ngrams(tokens: list[str], n: int) -> Counter:
            return Counter(tuple(tokens[i:i + n]) for i in range(len(tokens) - n + 1))

        ng_a = ngrams(tokens_a, n)
        ng_b = ngrams(tokens_b, n)

        if not ng_a or not ng_b:
            return 0.0

        overlap = sum((ng_a & ng_b).values())
        total = sum(ng_b.values())
        return overlap / total if total > 0 else 0.0

    def _error(self, reason: str) -> dict:
        return {
            "passed": False,
            "score": 0.0,
            "reason": reason,
            "status": "error",
            "evaluator": self.name,
        }
