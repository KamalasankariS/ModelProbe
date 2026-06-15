"""Hallucination detection evaluator.

Two strategies for catching hallucinations without paid APIs:

1. consistency — Re-queries the same model multiple times and measures response
   stability. Based on the self-consistency principle: a model that "knows" the
   answer will produce it reliably, while one that is guessing will vary across
   samples. Grounded in Wang et al., "Self-Consistency Improves Chain of Thought
   Reasoning in Language Models" (2022).

2. factual — Verifies factual claims in the output against the Wikidata knowledge
   graph via its free SPARQL endpoint. Catches fabricated facts, wrong dates,
   incorrect attributions, and other grounded hallucinations.

Config (consistency)::

    {
        "strategy": "consistency",
        "prompt": "What is the capital of France?",
        "model": "llama3",
        "endpoint": "http://localhost:11434/api/generate",
        "samples": 5,
        "threshold": 0.5
    }

Config (factual)::

    {
        "strategy": "factual",
        "claims": [
            {"subject": "Q142", "property": "P36", "expected_label": "Paris"},
            {"subject": "Q142", "property": "P30", "expected_label": "Europe"}
        ],
        "threshold": 0.5
    }

Usage::

    ev = HallucinationEvaluator()
    result = ev.evaluate(
        output="The capital of France is Paris.",
        config={
            "strategy": "consistency",
            "prompt": "What is the capital of France?",
            "model": "llama3",
            "endpoint": "http://localhost:11434/api/generate",
        },
    )
"""

from __future__ import annotations

import logging
import re
import time
from typing import Any, Dict, List, Optional

log = logging.getLogger(__name__)

WIKIDATA_ENTITY = "https://www.wikidata.org/wiki/Special:EntityData/{entity}.json"


class HallucinationEvaluator:

    name = "hallucination"

    def evaluate(
        self,
        output: str,
        expected: Optional[str] = None,
        config: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        config = config or {}
        strategy = config.get("strategy", "consistency")

        if strategy == "consistency":
            return self._consistency(output, config)
        elif strategy == "factual":
            return self._factual(output, config)
        else:
            return self._error(f"Unknown strategy '{strategy}'")

    # -- consistency strategy --------------------------------------------------

    def _consistency(self, original_output: str, config: dict) -> dict:
        prompt = config.get("prompt")
        if not prompt:
            return self._error("consistency strategy requires 'prompt' in config")

        model = config.get("model")
        if not model:
            return self._error("consistency strategy requires 'model' in config")

        endpoint = config.get("endpoint", "http://localhost:11434/api/generate")
        samples = int(config.get("samples", 5))
        threshold = float(config.get("threshold", 0.5))

        try:
            import httpx
        except ImportError:
            return self._error("httpx is required for consistency checks")

        responses = []
        for _ in range(samples):
            try:
                resp = httpx.post(
                    endpoint,
                    json={"model": model, "prompt": prompt, "stream": False},
                    timeout=120.0,
                )
                resp.raise_for_status()
                text = resp.json().get("response", "").strip()
                responses.append(text)
            except Exception as exc:
                log.warning("consistency sample failed: %s", exc)
                continue

        if len(responses) < 2:
            return self._error(f"Only got {len(responses)} response(s), need at least 2")

        score = self._agreement_score(original_output, responses)
        passed = score >= threshold

        if score >= 0.8:
            label = "high consistency"
        elif score >= 0.5:
            label = "moderate consistency"
        else:
            label = "low consistency (likely hallucination)"

        return {
            "passed": passed,
            "score": round(score, 4),
            "reason": f"{label} — agreement {score:.0%} across {len(responses)} samples",
            "status": "pass" if passed else "fail",
            "evaluator": self.name,
            "detail": {
                "strategy": "consistency",
                "samples_collected": len(responses),
                "agreement_score": round(score, 4),
            },
        }

    def _agreement_score(self, original: str, responses: List[str]) -> float:
        original_tokens = self._extract_key_tokens(original)
        if not original_tokens:
            return self._jaccard_avg(original, responses)

        scores = []
        for resp in responses:
            resp_tokens = self._extract_key_tokens(resp)
            if not original_tokens and not resp_tokens:
                scores.append(1.0)
                continue
            union = original_tokens | resp_tokens
            if not union:
                scores.append(1.0)
                continue
            intersection = original_tokens & resp_tokens
            scores.append(len(intersection) / len(union))

        return sum(scores) / len(scores) if scores else 0.0

    def _extract_key_tokens(self, text: str) -> set:
        tokens = set()
        numbers = re.findall(r'\b\d+(?:\.\d+)?\b', text)
        tokens.update(numbers)
        words = re.findall(r'\b[A-Z][a-z]{2,}\b', text)
        tokens.update(w.lower() for w in words)
        specific = re.findall(
            r'\b(?:True|False|true|false|yes|no|Yes|No|none|None|null)\b', text
        )
        tokens.update(s.lower() for s in specific)
        return tokens

    def _jaccard_avg(self, original: str, responses: List[str]) -> float:
        orig_words = set(original.lower().split())
        if not orig_words:
            return 0.0
        scores = []
        for resp in responses:
            resp_words = set(resp.lower().split())
            union = orig_words | resp_words
            if not union:
                scores.append(1.0)
                continue
            scores.append(len(orig_words & resp_words) / len(union))
        return sum(scores) / len(scores) if scores else 0.0

    # -- factual strategy (Wikidata verification) ------------------------------

    def _factual(self, output: str, config: dict) -> dict:
        claims = config.get("claims")
        if not claims or not isinstance(claims, list):
            return self._error("factual strategy requires 'claims' list in config")

        threshold = float(config.get("threshold", 0.5))

        try:
            import httpx
        except ImportError:
            return self._error("httpx is required for factual checks")

        verified = 0
        contradicted = 0
        unresolved = 0
        details = []

        for claim in claims:
            subject = claim.get("subject")
            prop = claim.get("property")
            expected_label = claim.get("expected_label", "")

            if not subject or not prop:
                unresolved += 1
                details.append({"claim": claim, "result": "invalid"})
                continue

            wikidata_values = self._query_wikidata(subject, prop)
            time.sleep(1.5)  # respect Wikidata rate limits

            if wikidata_values is None:
                unresolved += 1
                details.append({"claim": claim, "result": "query_failed"})
                continue

            output_lower = output.lower()
            expected_lower = expected_label.lower()

            found_in_output = expected_lower in output_lower if expected_lower else False
            matches_wikidata = any(
                expected_lower in v.lower() for v in wikidata_values
            ) if expected_lower else False

            if found_in_output and matches_wikidata:
                verified += 1
                details.append({"claim": claim, "result": "verified"})
            elif found_in_output and not matches_wikidata:
                contradicted += 1
                details.append({
                    "claim": claim,
                    "result": "contradicted",
                    "wikidata_values": wikidata_values[:5],
                })
            elif not found_in_output and matches_wikidata:
                # Output doesn't mention this claim — not a hallucination, just omission
                unresolved += 1
                details.append({"claim": claim, "result": "not_mentioned"})
            else:
                unresolved += 1
                details.append({"claim": claim, "result": "unresolved"})

        total_checked = verified + contradicted
        if total_checked == 0:
            return {
                "passed": False,
                "score": 0.0,
                "reason": f"No claims could be verified ({unresolved} unresolved)",
                "status": "skipped",
                "evaluator": self.name,
                "detail": {"strategy": "factual", "claims_detail": details},
            }

        score = verified / total_checked
        passed = score >= threshold

        return {
            "passed": passed,
            "score": round(score, 4),
            "reason": (
                f"{verified} verified, {contradicted} contradicted, "
                f"{unresolved} unresolved out of {len(claims)} claims"
            ),
            "status": "pass" if passed else "fail",
            "evaluator": self.name,
            "detail": {
                "strategy": "factual",
                "verified": verified,
                "contradicted": contradicted,
                "unresolved": unresolved,
                "claims_detail": details,
            },
        }

    def _query_wikidata(self, subject: str, prop: str) -> Optional[List[str]]:
        try:
            import httpx
            headers = {"User-Agent": "ModelProbe/0.1 (https://github.com/KamalasankariS/ModelProbe)"}

            resp = httpx.get(
                WIKIDATA_ENTITY.format(entity=subject),
                headers=headers,
                timeout=15.0,
            )
            resp.raise_for_status()
            data = resp.json()

            claims = (
                data.get("entities", {})
                .get(subject, {})
                .get("claims", {})
                .get(prop, [])
            )

            value_ids = []
            labels = []
            for claim in claims:
                snak = claim.get("mainsnak", {})
                datavalue = snak.get("datavalue", {})
                vtype = datavalue.get("type")
                value = datavalue.get("value")

                if vtype == "wikibase-entityid" and isinstance(value, dict):
                    value_ids.append(value.get("id"))
                elif vtype == "string" and isinstance(value, str):
                    labels.append(value)
                elif vtype == "quantity" and isinstance(value, dict):
                    labels.append(value.get("amount", "").lstrip("+"))

            for vid in value_ids[:5]:
                label = self._resolve_label(vid, headers)
                if label:
                    labels.append(label)

            return labels if labels else []
        except Exception as exc:
            log.warning("Wikidata query failed: %s", exc)
            return None

    def _resolve_label(self, entity_id: str, headers: dict) -> Optional[str]:
        try:
            import httpx
            resp = httpx.get(
                WIKIDATA_ENTITY.format(entity=entity_id),
                headers=headers,
                timeout=10.0,
            )
            resp.raise_for_status()
            data = resp.json()
            labels = (
                data.get("entities", {})
                .get(entity_id, {})
                .get("labels", {})
            )
            en = labels.get("en", {})
            return en.get("value") if en else None
        except Exception:
            return None

    # -- helpers ---------------------------------------------------------------

    def _error(self, reason: str) -> dict:
        return {
            "passed": False,
            "score": 0.0,
            "reason": reason,
            "status": "error",
            "evaluator": self.name,
        }
