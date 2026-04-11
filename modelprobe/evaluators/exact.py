"""Exact string match evaluator."""

from __future__ import annotations

from typing import Any, Dict, Optional


class ExactEvaluator:
    """Passes when output exactly equals expected.

    Config options::

        {
            "case_sensitive": bool  # default True
        }

    Usage::

        ev = ExactEvaluator()
        result = ev.evaluate(output="Hello", expected="Hello", config={})
    """

    name = "exact"

    def evaluate(
        self,
        output: str,
        expected: Optional[str] = None,
        config: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        config = config or {}
        case_sensitive = config.get("case_sensitive", True)

        if expected is None:
            return {
                "passed": False,
                "score": 0.0,
                "reason": "No expected output provided",
                "status": "error",
                "evaluator": self.name,
            }

        a = output if case_sensitive else output.lower()
        b = expected if case_sensitive else expected.lower()
        passed = a == b

        return {
            "passed": passed,
            "score": 1.0 if passed else 0.0,
            "reason": "Exact match" if passed else f"Expected {expected!r}, got {output!r}",
            "status": "pass" if passed else "fail",
            "evaluator": self.name,
        }
