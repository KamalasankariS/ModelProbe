"""Live evaluation endpoint for the Playground UI."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, Optional

from fastapi import APIRouter
from pydantic import BaseModel

import modelprobe
from modelprobe.evaluators import get_evaluator
from modelprobe.server.models.schemas import APIEnvelope

router = APIRouter()


class EvaluateRequest(BaseModel):
    output: str
    eval_type: str
    expected: Optional[str] = None
    config: Dict[str, Any] = {}


@router.post("/evaluate", response_model=APIEnvelope)
async def evaluate(payload: EvaluateRequest):
    try:
        evaluator = get_evaluator(payload.eval_type)
    except ValueError as exc:
        return APIEnvelope(
            data={"passed": False, "score": 0.0, "reason": str(exc), "status": "error", "evaluator": payload.eval_type},
            version=modelprobe.__version__,
            timestamp=datetime.now(timezone.utc),
        )

    result = evaluator.evaluate(
        output=payload.output,
        expected=payload.expected,
        config=payload.config,
    )

    return APIEnvelope(
        data=result,
        version=modelprobe.__version__,
        timestamp=datetime.now(timezone.utc),
    )
