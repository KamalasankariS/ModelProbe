"""ModelProbe evaluators.

Each evaluator accepts an output string and returns an EvalResult dict with
the shape::

    {
        "passed": bool,
        "score": float,       # 0.0 – 1.0
        "reason": str,
        "status": str,        # "pass" | "fail" | "error" | "skipped"
        "evaluator": str,
    }

Import by name::

    from modelprobe.evaluators import get_evaluator
    evaluator = get_evaluator("contains")
    result = evaluator.evaluate(output="hello world", config={"values": ["hello"]})
"""

from modelprobe.evaluators.exact import ExactEvaluator
from modelprobe.evaluators.contains import ContainsEvaluator
from modelprobe.evaluators.regex import RegexEvaluator
from modelprobe.evaluators.json_schema import JsonSchemaEvaluator
from modelprobe.evaluators.llm_judge import LLMJudgeEvaluator
from modelprobe.evaluators.hallucination import HallucinationEvaluator

_REGISTRY = {
    "exact": ExactEvaluator,
    "contains": ContainsEvaluator,
    "regex": RegexEvaluator,
    "json_schema": JsonSchemaEvaluator,
    "llm_judge": LLMJudgeEvaluator,
    "hallucination": HallucinationEvaluator,
}


def get_evaluator(eval_type: str):
    """Return an evaluator instance for the given type string.

    Args:
        eval_type: One of "exact", "contains", "regex", "json_schema", "llm_judge".

    Raises:
        ValueError: If the eval_type is not recognised.

    Usage::

        ev = get_evaluator("exact")
        result = ev.evaluate(output="hello", expected="hello", config={})
    """
    cls = _REGISTRY.get(eval_type)
    if cls is None:
        raise ValueError(
            f"Unknown eval_type '{eval_type}'. "
            f"Valid types: {', '.join(_REGISTRY)}"
        )
    return cls()


__all__ = [
    "ExactEvaluator",
    "ContainsEvaluator",
    "RegexEvaluator",
    "JsonSchemaEvaluator",
    "LLMJudgeEvaluator",
    "HallucinationEvaluator",
    "get_evaluator",
]
