"""Health check endpoint."""

from __future__ import annotations

import time
from datetime import datetime, timezone

from fastapi import APIRouter

import modelprobe
from modelprobe.server.models.schemas import APIEnvelope, HealthOut

router = APIRouter()

_start_time = time.monotonic()


@router.get("/health", response_model=APIEnvelope)
async def health():
    """Return server health status, version, and uptime."""
    from modelprobe.config import settings
    from modelprobe.server.db.database import get_engine
    from sqlalchemy import text

    db_status = "ok"
    try:
        engine = get_engine()
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
    except Exception as exc:
        db_status = f"error: {exc}"

    payload = HealthOut(
        version=modelprobe.__version__,
        mode=settings.mode,
        db_status=db_status,
        uptime_s=round(time.monotonic() - _start_time, 1),
    )

    return APIEnvelope(
        data=payload.model_dump(),
        version=modelprobe.__version__,
        timestamp=datetime.now(timezone.utc),
    )
