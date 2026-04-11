"""SQLAlchemy ORM models for the async server database."""

from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import JSON, Boolean, Column, DateTime, Float, ForeignKey, Integer, String, Text

from modelprobe.server.db.database import Base


class ServerRunRecord(Base):
    __tablename__ = "runs"

    id = Column(String(36), primary_key=True)
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


class ServerTestCaseRecord(Base):
    __tablename__ = "test_cases"

    id = Column(String(36), primary_key=True)
    suite = Column(String(255), nullable=False, index=True)
    test_case_id = Column(String(255), nullable=False, index=True)
    input = Column(Text, nullable=True)
    expected_output = Column(Text, nullable=True)
    eval_type = Column(String(64), nullable=False)
    eval_config = Column(JSON, nullable=False, default=dict)


class ServerEvalResultRecord(Base):
    __tablename__ = "eval_results"

    id = Column(String(36), primary_key=True)
    run_id = Column(String(36), ForeignKey("runs.id"), nullable=False, index=True)
    test_case_id = Column(String(255), nullable=False, index=True)
    passed = Column(Boolean, nullable=False)
    score = Column(Float, nullable=True)
    reason = Column(Text, nullable=True)
    status = Column(String(16), nullable=False, default="pass")
    evaluator = Column(String(64), nullable=False)
