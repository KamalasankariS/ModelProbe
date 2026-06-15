"""SQLite backend for ModelProbe using SQLAlchemy 2.x ORM."""

from __future__ import annotations

import json
import logging
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional
from uuid import uuid4

from sqlalchemy import (
    JSON,
    Boolean,
    Column,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    create_engine,
    event,
    text,
)
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

log = logging.getLogger(__name__)


class Base(DeclarativeBase):
    pass


class RunRecord(Base):
    __tablename__ = "runs"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid4()))
    trace_id = Column(String(36), nullable=False, index=True)
    parent_id = Column(String(36), nullable=True, index=True)
    suite = Column(String(255), nullable=False, index=True)
    version = Column(String(255), nullable=False, index=True)
    run_group = Column(String(255), nullable=True, index=True)
    commit_hash = Column(String(64), nullable=True)
    tags = Column(JSON, nullable=False, default=dict)
    input = Column(Text, nullable=True)
    output = Column(Text, nullable=True)
    status = Column(String(16), nullable=False, default="pass")
    latency_ms = Column(Float, nullable=True)
    token_count = Column(Integer, nullable=True)
    timestamp = Column(DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))


class TestCaseRecord(Base):
    __tablename__ = "test_cases"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid4()))
    suite = Column(String(255), nullable=False, index=True)
    test_case_id = Column(String(255), nullable=False, index=True)
    input = Column(Text, nullable=True)
    expected_output = Column(Text, nullable=True)
    eval_type = Column(String(64), nullable=False)
    eval_config = Column(JSON, nullable=False, default=dict)


class EvalResultRecord(Base):
    __tablename__ = "eval_results"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid4()))
    run_id = Column(String(36), ForeignKey("runs.id"), nullable=False, index=True)
    test_case_id = Column(String(255), nullable=False, index=True)
    passed = Column(Boolean, nullable=False)
    score = Column(Float, nullable=True)
    reason = Column(Text, nullable=True)
    status = Column(String(16), nullable=False, default="pass")
    evaluator = Column(String(64), nullable=False)


class SQLiteBackend:
    """Persistent local storage backend backed by a SQLite file.

    The database file and its parent directory are created on first use.
    All write operations are synchronous and thread-safe via SQLAlchemy's
    connection pool.

    Usage::

        backend = SQLiteBackend("/home/user/.modelprobe/modelprobe.db")
        backend.write_run({"id": "...", "suite": "my-agent", ...})
    """

    def __init__(self, db_path: str) -> None:
        path = Path(db_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        url = f"sqlite:///{path}"
        self._engine = create_engine(url, echo=False, future=True)

        @event.listens_for(self._engine, "connect")
        def set_sqlite_pragma(dbapi_conn, _connection_record):
            cursor = dbapi_conn.cursor()
            cursor.execute("PRAGMA journal_mode=WAL")
            cursor.execute("PRAGMA foreign_keys=ON")
            cursor.close()

        Base.metadata.create_all(self._engine)
        self._Session = sessionmaker(bind=self._engine, expire_on_commit=False)

    def _session(self) -> Session:
        return self._Session()

    def write_run(self, run: Dict[str, Any]) -> None:
        tags = run.get("tags", {})
        timestamp_raw = run.get("timestamp")
        if isinstance(timestamp_raw, str):
            try:
                timestamp = datetime.fromisoformat(timestamp_raw.replace("Z", "+00:00"))
            except ValueError:
                timestamp = datetime.now(timezone.utc)
        elif isinstance(timestamp_raw, datetime):
            timestamp = timestamp_raw
        else:
            timestamp = datetime.now(timezone.utc)

        record = RunRecord(
            id=run.get("id", str(uuid4())),
            trace_id=run["trace_id"],
            parent_id=run.get("parent_id"),
            suite=run["suite"],
            version=run["version"],
            run_group=run.get("run_group"),
            commit_hash=run.get("commit_hash"),
            tags=tags if isinstance(tags, dict) else {},
            input=_coerce_text(run.get("input")),
            output=_coerce_text(run.get("output")),
            status=run.get("status", "pass"),
            latency_ms=run.get("latency_ms"),
            token_count=run.get("token_count"),
            timestamp=timestamp,
        )
        with self._session() as session:
            session.merge(record)
            session.commit()

    def get_run(self, run_id: str) -> Optional[Dict[str, Any]]:
        with self._session() as session:
            rec = session.get(RunRecord, run_id)
            if rec is None:
                return None
            row = _run_to_dict(rec)
        row["steps"] = self._get_children(run_id)
        return row

    def _get_children(self, parent_id: str) -> List[Dict[str, Any]]:
        with self._session() as session:
            children = (
                session.query(RunRecord)
                .filter(RunRecord.parent_id == parent_id)
                .order_by(RunRecord.timestamp)
                .all()
            )
            return [_run_to_dict(c) for c in children]

    def list_runs(self, filters: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        filters = filters or {}
        with self._session() as session:
            q = session.query(RunRecord)
            if filters.get("suite"):
                q = q.filter(RunRecord.suite == filters["suite"])
            if filters.get("version"):
                q = q.filter(RunRecord.version == filters["version"])
            if filters.get("run_group"):
                q = q.filter(RunRecord.run_group == filters["run_group"])
            if filters.get("status"):
                q = q.filter(RunRecord.status == filters["status"])
            if filters.get("date_from"):
                q = q.filter(RunRecord.timestamp >= filters["date_from"])
            if filters.get("date_to"):
                q = q.filter(RunRecord.timestamp <= filters["date_to"])
            if filters.get("tag"):
                key, _, value = filters["tag"].partition(":")
                if not re.match(r"^[a-zA-Z_][a-zA-Z0-9_]*$", key):
                    return []
                q = q.filter(text(f"json_extract(tags, '$.{key}') = :val").bindparams(val=value))
            rows = q.order_by(RunRecord.timestamp.desc()).all()
            return [_run_to_dict(r) for r in rows]

    def write_eval_result(self, result: Dict[str, Any]) -> None:
        record = EvalResultRecord(
            id=result.get("id", str(uuid4())),
            run_id=result["run_id"],
            test_case_id=result["test_case_id"],
            passed=bool(result["passed"]),
            score=result.get("score"),
            reason=result.get("reason"),
            status=result.get("status", "pass"),
            evaluator=result["evaluator"],
        )
        with self._session() as session:
            session.merge(record)
            session.commit()

    def write_test_case(self, tc: Dict[str, Any]) -> None:
        record = TestCaseRecord(
            id=tc.get("id", str(uuid4())),
            suite=tc["suite"],
            test_case_id=tc["test_case_id"],
            input=_coerce_text(tc.get("input")),
            expected_output=_coerce_text(tc.get("expected_output")),
            eval_type=tc["eval_type"],
            eval_config=tc.get("eval_config", {}),
        )
        with self._session() as session:
            session.merge(record)
            session.commit()

    def list_test_cases(self, suite: str) -> List[Dict[str, Any]]:
        with self._session() as session:
            rows = session.query(TestCaseRecord).filter(TestCaseRecord.suite == suite).all()
            return [_tc_to_dict(r) for r in rows]

    def list_eval_results(self, run_id: str) -> List[Dict[str, Any]]:
        with self._session() as session:
            rows = (
                session.query(EvalResultRecord)
                .filter(EvalResultRecord.run_id == run_id)
                .all()
            )
            return [_eval_to_dict(r) for r in rows]

    def list_suites(self) -> List[str]:
        with self._session() as session:
            rows = session.query(RunRecord.suite).distinct().all()
            return [r[0] for r in rows]


def _coerce_text(value: Any) -> Optional[str]:
    if value is None:
        return None
    if isinstance(value, str):
        return value
    return json.dumps(value)


def _run_to_dict(rec: RunRecord) -> Dict[str, Any]:
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


def _tc_to_dict(rec: TestCaseRecord) -> Dict[str, Any]:
    return {
        "id": rec.id,
        "suite": rec.suite,
        "test_case_id": rec.test_case_id,
        "input": rec.input,
        "expected_output": rec.expected_output,
        "eval_type": rec.eval_type,
        "eval_config": rec.eval_config or {},
    }


def _eval_to_dict(rec: EvalResultRecord) -> Dict[str, Any]:
    return {
        "id": rec.id,
        "run_id": rec.run_id,
        "test_case_id": rec.test_case_id,
        "passed": rec.passed,
        "score": rec.score,
        "reason": rec.reason,
        "status": rec.status,
        "evaluator": rec.evaluator,
    }
