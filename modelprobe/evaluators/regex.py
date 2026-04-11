"""Regular expression evaluator."""

from __future__ import annotations

import re
from typing import Any, Dict, Optional


class RegexEvaluator:
    """Passes when output matches the provided regular expression.

    Config options::

        {
            "pattern": str,   # regex pattern (required)
            "flags": int      # re module flags, default 0
        }

    Usage::

        ev = RegexEvaluator()
        result = ev.evaluate(
            output="Order #12345 confirmed",
            config={"pattern": r"Order #\d+"},
        )
    """

    name = "regex"

    def evaluate(
        self,
        output: str,
        expected: Optional[str] = None,
        config: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        config = config or {}
        pattern = config.get("pattern")
        flags = config.get("flags", 0)

        if not pattern:
            return {
                "passed": False,
                "score": 0.0,
                "reason": "Config missing required 'pattern' field",
                "status": "error",
                "evaluator": self.name,
            }

        try:
            match = re.search(pattern, output, flags)
        except re.error as exc:
            return {
                "passed": False,
                "score": 0.0,
                "reason": f"Invalid regex pattern: {exc}",
                "status": "error",
                "evaluator": self.name,
            }

        passed = match is not None
        return {
            "passed": passed,
            "score": 1.0 if passed else 0.0,
            "reason": f"Pattern matched: {match.group()!r}" if passed else f"Pattern {pattern!r} not found",
            "status": "pass" if passed else "fail",
            "evaluator": self.name,
        }
