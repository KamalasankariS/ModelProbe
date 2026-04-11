"""Substring containment evaluator."""

from __future__ import annotations

from typing import Any, Dict, List, Optional


class ContainsEvaluator:
    """Passes when output contains one or all of the specified substrings.

    Config options::

        {
            "values": List[str],   # substrings to look for (required)
            "mode": "any" | "all"  # default "any"
        }

    Usage::

        ev = ContainsEvaluator()
        result = ev.evaluate(
            output="The invoice total is $500",
            config={"values": ["invoice", "$500"], "mode": "all"},
        )
    """

    name = "contains"

    def evaluate(
        self,
        output: str,
        expected: Optional[str] = None,
        config: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        config = config or {}
        values: List[str] = config.get("values", [])
        mode: str = config.get("mode", "any")

        if not values:
            return {
                "passed": False,
                "score": 0.0,
                "reason": "Config missing required 'values' list",
                "status": "error",
                "evaluator": self.name,
            }

        hits = [v for v in values if v in output]
        hit_count = len(hits)
        total = len(values)

        if mode == "all":
            passed = hit_count == total
            score = hit_count / total
            if passed:
                reason = f"All {total} substring(s) found"
            else:
                missing = [v for v in values if v not in output]
                reason = f"Missing substring(s): {missing}"
        else:
            passed = hit_count > 0
            score = 1.0 if passed else 0.0
            reason = f"Found {hits}" if passed else f"None of {values} found in output"

        return {
            "passed": passed,
            "score": round(score, 4),
            "reason": reason,
            "status": "pass" if passed else "fail",
            "evaluator": self.name,
        }
