"""Run submission and retrieval endpoints."""

from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from typing import List, Optional
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

import modelprobe
from modelprobe.server.db.database import get_session
from modelprobe.server.db.models import ServerEvalResultRecord, ServerRunRecord
from modelprobe.server.models.schemas import (
    APIEnvelope,
    EvalResultIn,
    EvalResultOut,
    RunIn,
    RunOut,
)

router = APIRouter()


def _record_to_dict(rec: ServerRunRecord) -> dict:
    ts = rec.timestamp
    if ts is not None and ts.tzinfo is None:
        ts = ts.replace(tzinfo=timezone.utc)
    return {
        "id": rec.id,
        "trace_id": rec.trace_id,
        "parent_id": rec.parent_id,
        "suite": rec.suite,
        "version": rec.version,
        "run_group": rec.run_group,
        "commit_hash": rec.commit_hash,
        "tags": rec.tags or {},
        "input": rec.input,
        "output": rec.output,
        "status": rec.status,
        "latency_ms": rec.latency_ms,
        "token_count": rec.token_count,
        "timestamp": ts.isoformat() if ts else None,
        "steps": [],
    }


def _envelope(data, version=None) -> APIEnvelope:
    return APIEnvelope(
        data=data,
        version=version or modelprobe.__version__,
        timestamp=datetime.now(timezone.utc),
    )


@router.post("/runs", response_model=APIEnvelope, status_code=201)
async def submit_run(payload: RunIn, session: AsyncSession = Depends(get_session)):
    """Submit a single run record."""
    rec = ServerRunRecord(
        id=payload.id,
        trace_id=payload.trace_id,
        parent_id=payload.parent_id,
        suite=payload.suite,
        version=payload.version,
        run_group=payload.run_group,
        commit_hash=payload.commit_hash,
        tags=payload.tags,
        input=payload.input,
        output=payload.output,
        status=payload.status,
        latency_ms=payload.latency_ms,
        token_count=payload.token_count,
        timestamp=payload.timestamp or datetime.now(timezone.utc),
    )
    session.add(rec)
    await session.commit()
    return _envelope(_record_to_dict(rec))


@router.get("/runs", response_model=APIEnvelope)
async def list_runs(
    suite: Optional[str] = None,
    version: Optional[str] = None,
    run_group: Optional[str] = None,
    status: Optional[str] = None,
    tag: Optional[str] = None,
    date_from: Optional[datetime] = None,
    date_to: Optional[datetime] = None,
    limit: int = Query(100, le=1000),
    offset: int = Query(0, ge=0),
    session: AsyncSession = Depends(get_session),
):
    """List runs with optional filters."""
    from sqlalchemy import select

    q = select(ServerRunRecord)
    if suite:
        q = q.where(ServerRunRecord.suite == suite)
    if version:
        q = q.where(ServerRunRecord.version == version)
    if run_group:
        q = q.where(ServerRunRecord.run_group == run_group)
    if status:
        q = q.where(ServerRunRecord.status == status)
    if date_from:
        q = q.where(ServerRunRecord.timestamp >= date_from)
    if date_to:
        q = q.where(ServerRunRecord.timestamp <= date_to)
    if tag:
        key, _, value = tag.partition(":")
        if not re.match(r"^[a-zA-Z_][a-zA-Z0-9_]*$", key):
            return _envelope([])
        q = q.where(text(f"json_extract(tags, '$.{key}') = :tag_val").bindparams(tag_val=value))

    q = q.order_by(ServerRunRecord.timestamp.desc()).offset(offset).limit(limit)
    result = await session.execute(q)
    rows = result.scalars().all()
    return _envelope([_record_to_dict(r) for r in rows])


@router.get("/runs/{run_id}", response_model=APIEnvelope)
async def get_run(run_id: str, session: AsyncSession = Depends(get_session)):
    """Fetch a run by ID, including its nested steps."""
    from sqlalchemy import select

    rec = await session.get(ServerRunRecord, run_id)
    if rec is None:
        raise HTTPException(status_code=404, detail="Run not found")

    data = _record_to_dict(rec)

    children_q = select(ServerRunRecord).where(ServerRunRecord.parent_id == run_id).order_by(ServerRunRecord.timestamp)
    children_result = await session.execute(children_q)
    data["steps"] = [_record_to_dict(c) for c in children_result.scalars().all()]

    return _envelope(data)


@router.get("/runs/{run_id}/eval-results", response_model=APIEnvelope)
async def get_run_eval_results(run_id: str, session: AsyncSession = Depends(get_session)):
    """Return all eval results for a given run."""
    from sqlalchemy import select

    q = select(ServerEvalResultRecord).where(ServerEvalResultRecord.run_id == run_id)
    result = await session.execute(q)
    rows = result.scalars().all()

    data = [
        {
            "id": r.id,
            "run_id": r.run_id,
            "test_case_id": r.test_case_id,
            "passed": r.passed,
            "score": r.score,
            "reason": r.reason,
            "status": r.status,
            "evaluator": r.evaluator,
        }
        for r in rows
    ]
    return _envelope(data)


@router.post("/eval-results", response_model=APIEnvelope, status_code=201)
async def submit_eval_result(payload: EvalResultIn, session: AsyncSession = Depends(get_session)):
    """Submit an eval result."""
    rec = ServerEvalResultRecord(
        id=payload.id,
        run_id=payload.run_id,
        test_case_id=payload.test_case_id,
        passed=payload.passed,
        score=payload.score,
        reason=payload.reason,
        status=payload.status,
        evaluator=payload.evaluator,
    )
    session.add(rec)
    await session.commit()
    return _envelope(
        {
            "id": rec.id,
            "run_id": rec.run_id,
            "test_case_id": rec.test_case_id,
            "passed": rec.passed,
            "score": rec.score,
            "reason": rec.reason,
            "status": rec.status,
            "evaluator": rec.evaluator,
        }
    )
