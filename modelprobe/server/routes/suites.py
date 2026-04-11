"""Suite management, version comparison, and regression detection endpoints."""

from __future__ import annotations

from collections import defaultdict
from datetime import datetime, timezone
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

import modelprobe
from modelprobe.server.db.database import get_session
from modelprobe.server.db.models import ServerEvalResultRecord, ServerRunRecord, ServerTestCaseRecord
from modelprobe.server.models.schemas import (
    APIEnvelope,
    CompareOut,
    RegressionOut,
    SuiteOut,
    TestCaseIn,
    TestCaseOut,
    VersionCompareResult,
)

router = APIRouter()


def _envelope(data) -> APIEnvelope:
    return APIEnvelope(
        data=data,
        version=modelprobe.__version__,
        timestamp=datetime.now(timezone.utc),
    )


@router.get("/suites", response_model=APIEnvelope)
async def list_suites(session: AsyncSession = Depends(get_session)):
    """List all suites with their latest version and pass rate."""
    q = select(ServerRunRecord.suite, ServerRunRecord.version, ServerRunRecord.status, ServerRunRecord.timestamp)
    result = await session.execute(q)
    rows = result.all()

    suites: dict[str, dict] = {}
    for suite, version, status, timestamp in rows:
        if suite not in suites:
            suites[suite] = {"versions": set(), "statuses": [], "last_run": timestamp}
        suites[suite]["versions"].add(version)
        suites[suite]["statuses"].append(status)
        if timestamp and (suites[suite]["last_run"] is None or timestamp > suites[suite]["last_run"]):
            suites[suite]["last_run"] = timestamp

    output = []
    for name, info in suites.items():
        statuses = info["statuses"]
        total = len(statuses)
        passed = sum(1 for s in statuses if s == "pass")
        pass_rate = passed / total if total > 0 else 0.0

        output.append(
            SuiteOut(
                name=name,
                latest_version=max(info["versions"]) if info["versions"] else None,
                pass_rate=round(pass_rate, 4),
                has_regressions=False,
                last_run=info["last_run"],
                version_count=len(info["versions"]),
            ).model_dump()
        )

    output.sort(key=lambda x: x["pass_rate"])
    return _envelope(output)


@router.get("/suites/{name}", response_model=APIEnvelope)
async def get_suite(name: str, session: AsyncSession = Depends(get_session)):
    """Return suite detail with full version history and per-version pass rates."""
    q = select(ServerRunRecord.version, ServerRunRecord.status).where(ServerRunRecord.suite == name)
    result = await session.execute(q)
    rows = result.all()

    if not rows:
        raise HTTPException(status_code=404, detail=f"Suite '{name}' not found")

    version_stats: dict[str, dict] = {}
    for version, status in rows:
        if version not in version_stats:
            version_stats[version] = {"total": 0, "passed": 0}
        version_stats[version]["total"] += 1
        if status == "pass":
            version_stats[version]["passed"] += 1

    history = [
        {
            "version": v,
            "total": s["total"],
            "passed": s["passed"],
            "pass_rate": round(s["passed"] / s["total"], 4) if s["total"] > 0 else 0.0,
        }
        for v, s in version_stats.items()
    ]

    tc_result = await session.execute(
        select(ServerTestCaseRecord).where(ServerTestCaseRecord.suite == name)
    )
    test_cases = [
        {
            "id": tc.id,
            "test_case_id": tc.test_case_id,
            "input": tc.input,
            "expected_output": tc.expected_output,
            "eval_type": tc.eval_type,
            "eval_config": tc.eval_config,
        }
        for tc in tc_result.scalars().all()
    ]

    return _envelope({"name": name, "version_history": history, "test_cases": test_cases})


@router.post("/suites/{name}/test-cases", response_model=APIEnvelope, status_code=201)
async def upsert_test_case(name: str, payload: TestCaseIn, session: AsyncSession = Depends(get_session)):
    """Create or update a test case for a suite."""
    existing_q = select(ServerTestCaseRecord).where(
        ServerTestCaseRecord.suite == name,
        ServerTestCaseRecord.test_case_id == payload.test_case_id,
    )
    existing_result = await session.execute(existing_q)
    existing = existing_result.scalar_one_or_none()

    if existing:
        existing.input = payload.input
        existing.expected_output = payload.expected_output
        existing.eval_type = payload.eval_type
        existing.eval_config = payload.eval_config
        tc = existing
    else:
        tc = ServerTestCaseRecord(
            id=payload.id,
            suite=name,
            test_case_id=payload.test_case_id,
            input=payload.input,
            expected_output=payload.expected_output,
            eval_type=payload.eval_type,
            eval_config=payload.eval_config or {},
        )
        session.add(tc)

    await session.commit()
    return _envelope(TestCaseOut(
        id=tc.id,
        suite=tc.suite,
        test_case_id=tc.test_case_id,
        input=tc.input,
        expected_output=tc.expected_output,
        eval_type=tc.eval_type,
        eval_config=tc.eval_config or {},
    ).model_dump())


@router.get("/suites/{name}/test-cases", response_model=APIEnvelope)
async def list_test_cases(name: str, session: AsyncSession = Depends(get_session)):
    """Return all test cases for a suite."""
    q = select(ServerTestCaseRecord).where(ServerTestCaseRecord.suite == name)
    result = await session.execute(q)
    return _envelope([
        TestCaseOut(
            id=tc.id,
            suite=tc.suite,
            test_case_id=tc.test_case_id,
            input=tc.input,
            expected_output=tc.expected_output,
            eval_type=tc.eval_type,
            eval_config=tc.eval_config or {},
        ).model_dump()
        for tc in result.scalars().all()
    ])


@router.get("/suites/{name}/compare", response_model=APIEnvelope)
async def compare_versions(
    name: str,
    v1: str = Query(..., description="Baseline version"),
    v2: str = Query(..., description="Candidate version"),
    session: AsyncSession = Depends(get_session),
):
    """Return a per-test-case diff between two versions of a suite.

    Response keys: regressed, improved, unchanged, new, removed.
    Each entry includes v1 and v2 result details keyed by test_case_id.
    """
    v1_results = await _get_version_results(session, name, v1)
    v2_results = await _get_version_results(session, name, v2)

    all_tc_ids = set(v1_results) | set(v2_results)

    regressed, improved, unchanged, new_cases, removed = [], [], [], [], []

    for tc_id in all_tc_ids:
        r1 = v1_results.get(tc_id)
        r2 = v2_results.get(tc_id)

        tc_info = await _get_test_case_info(session, name, tc_id)

        row = VersionCompareResult(
            test_case_id=tc_id,
            input=tc_info.get("input") if tc_info else None,
            expected_output=tc_info.get("expected_output") if tc_info else None,
            v1_status=r1["status"] if r1 else None,
            v1_score=r1["score"] if r1 else None,
            v1_reason=r1["reason"] if r1 else None,
            v2_status=r2["status"] if r2 else None,
            v2_score=r2["score"] if r2 else None,
            v2_reason=r2["reason"] if r2 else None,
        )

        if r1 is None:
            new_cases.append(row.model_dump())
        elif r2 is None:
            removed.append(row.model_dump())
        else:
            v1_pass = r1["status"] == "pass"
            v2_pass = r2["status"] == "pass"
            if v1_pass and not v2_pass:
                regressed.append(row.model_dump())
            elif not v1_pass and v2_pass:
                improved.append(row.model_dump())
            else:
                unchanged.append(row.model_dump())

    return _envelope(
        CompareOut(
            suite=name,
            v1=v1,
            v2=v2,
            regressed=regressed,
            improved=improved,
            unchanged=unchanged,
            new=new_cases,
            removed=removed,
        ).model_dump()
    )


@router.get("/suites/{name}/regressions", response_model=APIEnvelope)
async def get_regressions(name: str, session: AsyncSession = Depends(get_session)):
    """Return test cases where pass rate dropped vs the previous version, sorted by severity."""
    versions_q = (
        select(ServerRunRecord.version, func.max(ServerRunRecord.timestamp).label("latest"))
        .where(ServerRunRecord.suite == name)
        .group_by(ServerRunRecord.version)
        .order_by(func.max(ServerRunRecord.timestamp).desc())
    )
    versions_result = await session.execute(versions_q)
    versions = [row[0] for row in versions_result.all()]

    if len(versions) < 2:
        return _envelope([])

    current_v, previous_v = versions[0], versions[1]

    current_results = await _get_version_results(session, name, current_v)
    previous_results = await _get_version_results(session, name, previous_v)

    regressions = []
    for tc_id in set(current_results) & set(previous_results):
        prev_pass = 1.0 if previous_results[tc_id]["status"] == "pass" else 0.0
        curr_pass = 1.0 if current_results[tc_id]["status"] == "pass" else 0.0
        if curr_pass < prev_pass:
            severity = prev_pass - curr_pass
            tc_info = await _get_test_case_info(session, name, tc_id)
            regressions.append(
                RegressionOut(
                    test_case_id=tc_id,
                    previous_pass_rate=prev_pass,
                    current_pass_rate=curr_pass,
                    severity=severity,
                    input=tc_info.get("input") if tc_info else None,
                    expected_output=tc_info.get("expected_output") if tc_info else None,
                ).model_dump()
            )

    regressions.sort(key=lambda x: x["severity"], reverse=True)
    return _envelope(regressions)


async def _get_version_results(session: AsyncSession, suite: str, version: str) -> dict:
    """Return a dict mapping test_case_id to its most recent eval result for the given version."""
    runs_q = (
        select(ServerRunRecord.id)
        .where(ServerRunRecord.suite == suite, ServerRunRecord.version == version)
    )
    runs_result = await session.execute(runs_q)
    run_ids = [r[0] for r in runs_result.all()]

    if not run_ids:
        return {}

    evals_q = select(ServerEvalResultRecord).where(ServerEvalResultRecord.run_id.in_(run_ids))
    evals_result = await session.execute(evals_q)
    evals = evals_result.scalars().all()

    by_tc: dict = {}
    for ev in evals:
        if ev.test_case_id not in by_tc:
            by_tc[ev.test_case_id] = {"status": ev.status, "score": ev.score, "reason": ev.reason}

    return by_tc


async def _get_test_case_info(session: AsyncSession, suite: str, test_case_id: str) -> dict:
    q = select(ServerTestCaseRecord).where(
        ServerTestCaseRecord.suite == suite,
        ServerTestCaseRecord.test_case_id == test_case_id,
    )
    result = await session.execute(q)
    tc = result.scalar_one_or_none()
    if tc is None:
        return {}
    return {"input": tc.input, "expected_output": tc.expected_output}
