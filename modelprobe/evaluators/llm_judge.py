"""LLM-as-judge evaluator.

Sends the model output and a rubric to an OpenAI-compatible endpoint and
parses a pass/fail verdict plus a reason string from the response.

Timeout contract:
    - Default timeout: 10 seconds (minimum 5 seconds, configurable via config).
    - On timeout  -> status="skipped", reason="llm_judge timed out"
    - On any LLM error -> status="skipped", reason="llm_judge unavailable: {error}"
    - A skipped result never becomes status="fail".

Config options::

    {
        "model": str,       # model name, e.g. "gpt-4o-mini"
        "endpoint": str,    # OpenAI-compatible endpoint URL (optional, reads env)
        "rubric": str,      # evaluation instructions (required)
        "threshold": float, # score threshold for pass, default 0.5
        "timeout_s": float  # request timeout, default 10.0, minimum 5.0
    }

Usage::

    ev = LLMJudgeEvaluator()
    result = ev.evaluate(
        output="The capital of France is Paris.",
        config={
            "model": "gpt-4o-mini",
            "rubric": "Answer is factually correct and concise.",
        },
    )
"""

from __future__ import annotations

import json
import logging
import os
from typing import Any, Dict, Optional

log = logging.getLogger(__name__)

_SYSTEM_PROMPT = """You are an AI evaluation judge.

You will be given an AI output and a rubric. Score the output on a scale of
0.0 to 1.0 and decide if it passes.

Respond with JSON only — no markdown, no prose — in exactly this shape:
{"passed": true|false, "score": 0.0-1.0, "reason": "one sentence explanation"}"""

_USER_TEMPLATE = """Rubric: {rubric}

Output to evaluate:
{output}"""


class LLMJudgeEvaluator:
    """Evaluates model output against a rubric using another LLM."""

    name = "llm_judge"

    def evaluate(
        self,
        output: str,
        expected: Optional[str] = None,
        config: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        config = config or {}

        rubric = config.get("rubric")
        if not rubric:
            return self._skipped("Config missing required 'rubric' field")

        from modelprobe.config import settings

        endpoint = config.get("endpoint") or settings.llm_endpoint
        api_key = config.get("api_key") or settings.llm_api_key or os.environ.get("MODELPROBE_LLM_API_KEY")
        model = config.get("model", "gpt-4o-mini")
        threshold = float(config.get("threshold", 0.5))
        timeout_s = max(5.0, float(config.get("timeout_s", 10.0)))

        payload = {
            "model": model,
            "messages": [
                {"role": "system", "content": _SYSTEM_PROMPT},
                {"role": "user", "content": _USER_TEMPLATE.format(rubric=rubric, output=output)},
            ],
            "temperature": 0.0,
            "max_tokens": 256,
        }

        headers = {"Content-Type": "application/json"}
        if api_key:
            headers["Authorization"] = f"Bearer {api_key}"

        try:
            import httpx
            response = httpx.post(
                endpoint,
                json=payload,
                headers=headers,
                timeout=timeout_s,
            )
            response.raise_for_status()
        except httpx.TimeoutException:
            return self._skipped("llm_judge timed out")
        except Exception as exc:
            return self._skipped(f"llm_judge unavailable: {exc}")

        try:
            body = response.json()
            content = body["choices"][0]["message"]["content"].strip()
            verdict = json.loads(content)
            passed = bool(verdict["passed"])
            score = float(verdict.get("score", 1.0 if passed else 0.0))
            reason = str(verdict.get("reason", ""))

            if score < threshold:
                passed = False

            return {
                "passed": passed,
                "score": round(score, 4),
                "reason": reason,
                "status": "pass" if passed else "fail",
                "evaluator": self.name,
            }
        except Exception as exc:
            return self._skipped(f"llm_judge response parse error: {exc}")

    def _skipped(self, reason: str) -> Dict[str, Any]:
        return {
            "passed": False,
            "score": 0.0,
            "reason": reason,
            "status": "skipped",
            "evaluator": self.name,
        }
