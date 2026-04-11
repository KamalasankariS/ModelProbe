"""Pydantic v2 request and response schemas for the ModelProbe REST API."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Literal, Optional
from uuid import uuid4

from pydantic import BaseModel, Field


RunStatus = Literal["pass", "fail", "error", "skipped"]


class RunIn(BaseModel):
    """Payload for submitting a single run record."""

    id: str = Field(default_factory=lambda: str(uuid4()))
    trace_id: str = Field(default_factory=lambda: str(uuid4()))
    parent_id: Optional[str] = None
    suite: str
    version: str
    run_group: Optional[str] = None
    commit_hash: Optional[str] = None
    tags: Dict[str, str] = Field(default_factory=dict)
    input: Optional[str] = None
    output: Optional[str] = None
    status: RunStatus = "pass"
    latency_ms: Optional[float] = None
    token_count: Optional[int] = None
    timestamp: Optional[datetime] = None


class RunOut(BaseModel):
    """Full run record returned from the API."""

    id: str
    trace_id: str
    parent_id: Optional[str] = None
    suite: str
    version: str
    run_group: Optional[str] = None
    commit_hash: Optional[str] = None
    tags: Dict[str, str] = Field(default_factory=dict)
    input: Optional[str] = None
    output: Optional[str] = None
    status: RunStatus
    latency_ms: Optional[float] = None
    token_count: Optional[int] = None
    timestamp: Optional[datetime] = None
    steps: List["RunOut"] = Field(default_factory=list)


class EvalResultIn(BaseModel):
    """Payload for submitting an eval result."""

    id: str = Field(default_factory=lambda: str(uuid4()))
    run_id: str
    test_case_id: str
    passed: bool
    score: Optional[float] = None
    reason: Optional[str] = None
    status: RunStatus = "pass"
    evaluator: str


class EvalResultOut(BaseModel):
    """Eval result returned from the API."""

    id: str
    run_id: str
    test_case_id: str
    passed: bool
    score: Optional[float] = None
    reason: Optional[str] = None
    status: RunStatus
    evaluator: str


class TestCaseIn(BaseModel):
    """Payload for creating or updating a test case."""

    id: str = Field(default_factory=lambda: str(uuid4()))
    suite: str
    test_case_id: str
    input: Optional[str] = None
    expected_output: Optional[str] = None
    eval_type: str
    eval_config: Dict[str, Any] = Field(default_factory=dict)


class TestCaseOut(BaseModel):
    """Test case record returned from the API."""

    id: str
    suite: str
    test_case_id: str
    input: Optional[str] = None
    expected_output: Optional[str] = None
    eval_type: str
    eval_config: Dict[str, Any]


class SuiteOut(BaseModel):
    """Summary of a suite with its latest version stats."""

    name: str
    latest_version: Optional[str] = None
    pass_rate: Optional[float] = None
    has_regressions: bool = False
    last_run: Optional[datetime] = None
    version_count: int = 0


class VersionCompareResult(BaseModel):
    """Per-test-case diff between two versions of a suite."""

    test_case_id: str
    input: Optional[str] = None
    expected_output: Optional[str] = None
    v1_status: Optional[str] = None
    v1_score: Optional[float] = None
    v1_reason: Optional[str] = None
    v2_status: Optional[str] = None
    v2_score: Optional[float] = None
    v2_reason: Optional[str] = None


class CompareOut(BaseModel):
    """Full version comparison result."""

    suite: str
    v1: str
    v2: str
    regressed: List[VersionCompareResult] = Field(default_factory=list)
    improved: List[VersionCompareResult] = Field(default_factory=list)
    unchanged: List[VersionCompareResult] = Field(default_factory=list)
    new: List[VersionCompareResult] = Field(default_factory=list)
    removed: List[VersionCompareResult] = Field(default_factory=list)


class RegressionOut(BaseModel):
    """A test case that regressed relative to the previous version."""

    test_case_id: str
    previous_pass_rate: float
    current_pass_rate: float
    severity: float
    input: Optional[str] = None
    expected_output: Optional[str] = None


class HealthOut(BaseModel):
    """Server health check response."""

    version: str
    mode: str
    db_status: str
    uptime_s: float


class APIEnvelope(BaseModel):
    """Standard response wrapper for all API responses."""

    data: Any
    version: str
    timestamp: datetime
    request_id: str = Field(default_factory=lambda: str(uuid4()))
