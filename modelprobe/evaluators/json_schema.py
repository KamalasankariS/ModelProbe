"""JSON Schema evaluator."""

from __future__ import annotations

import json
from typing import Any, Dict, Optional


class JsonSchemaEvaluator:
    """Validates that the output is valid JSON conforming to a JSON Schema.

    A parse failure produces status="error", not status="fail", because the
    evaluator cannot make a correctness judgement on non-JSON output.

    Config options::

        {
            "schema": dict   # JSON Schema object (required)
        }

    Usage::

        ev = JsonSchemaEvaluator()
        result = ev.evaluate(
            output='{"name": "Alice", "age": 30}',
            config={"schema": {"type": "object", "required": ["name", "age"]}},
        )
    """

    name = "json_schema"

    def evaluate(
        self,
        output: str,
        expected: Optional[str] = None,
        config: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        config = config or {}
        schema = config.get("schema")

        if schema is None:
            return {
                "passed": False,
                "score": 0.0,
                "reason": "Config missing required 'schema' field",
                "status": "error",
                "evaluator": self.name,
            }

        try:
            data = json.loads(output)
        except (json.JSONDecodeError, ValueError) as exc:
            return {
                "passed": False,
                "score": 0.0,
                "reason": f"Output is not valid JSON: {exc}",
                "status": "error",
                "evaluator": self.name,
            }

        try:
            import jsonschema
            jsonschema.validate(instance=data, schema=schema)
        except jsonschema.ValidationError as exc:
            return {
                "passed": False,
                "score": 0.0,
                "reason": f"Schema validation failed: {exc.message}",
                "status": "fail",
                "evaluator": self.name,
            }
        except Exception as exc:
            return {
                "passed": False,
                "score": 0.0,
                "reason": f"Schema validation error: {exc}",
                "status": "error",
                "evaluator": self.name,
            }

        return {
            "passed": True,
            "score": 1.0,
            "reason": "Output validates against schema",
            "status": "pass",
            "evaluator": self.name,
        }
