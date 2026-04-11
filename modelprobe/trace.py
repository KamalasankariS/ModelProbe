"""ModelProbe trace decorator.

Wraps sync and async callables, capturing inputs, outputs, latency,
token counts, and exceptions.  Supports nested traces via a thread-local
context stack, producing a parent/child run tree sharing a single trace_id.

Usage::

    from modelprobe import trace

    @trace(suite="invoice-agent", version="v1")
    def call_llm(prompt):
        return model(prompt)

    @trace(suite="invoice-agent", version="v1", tags={"feature": "invoice"})
    async def run_agent(query):
        result = await call_llm(query)
        return result
"""

from __future__ import annotations

import asyncio
import functools
import inspect
import logging
import threading
import time
from datetime import datetime, timezone
from typing import Any, Callable, Dict, Optional
from uuid import uuid4

log = logging.getLogger(__name__)

_ctx = threading.local()


def _get_stack() -> list:
    if not hasattr(_ctx, "stack"):
        _ctx.stack = []
    return _ctx.stack


def _extract_token_count(result: Any) -> Optional[int]:
    """Pull token count from common LLM response shapes without raising."""
    try:
        if hasattr(result, "usage") and result.usage is not None:
            usage = result.usage
            if hasattr(usage, "total_tokens"):
                return int(usage.total_tokens)
            if hasattr(usage, "completion_tokens") and hasattr(usage, "prompt_tokens"):
                return int(usage.completion_tokens + usage.prompt_tokens)
        if isinstance(result, dict):
            usage = result.get("usage", {})
            if isinstance(usage, dict):
                return usage.get("total_tokens")
    except Exception:
        pass
    return None


def _coerce_str(value: Any) -> Optional[str]:
    if value is None:
        return None
    if isinstance(value, str):
        return value
    try:
        import json
        return json.dumps(value)
    except Exception:
        return str(value)


def _build_run(
    run_id: str,
    trace_id: str,
    parent_id: Optional[str],
    suite: str,
    version: str,
    run_group: Optional[str],
    commit_hash: Optional[str],
    tags: Dict[str, str],
    input_value: Any,
    output_value: Any,
    status: str,
    latency_ms: float,
    token_count: Optional[int],
) -> Dict[str, Any]:
    return {
        "id": run_id,
        "trace_id": trace_id,
        "parent_id": parent_id,
        "suite": suite,
        "version": version,
        "run_group": run_group,
        "commit_hash": commit_hash,
        "tags": tags,
        "input": _coerce_str(input_value),
        "output": _coerce_str(output_value),
        "status": status,
        "latency_ms": round(latency_ms, 3),
        "token_count": token_count,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "steps": [],
    }


def trace(
    suite: str,
    version: str,
    run_group: Optional[str] = None,
    commit_hash: Optional[str] = None,
    tags: Optional[Dict[str, str]] = None,
) -> Callable:
    """Decorator that records every call as a Run in ModelProbe storage.

    Can be applied to any sync or async callable.  Nested ``@trace``
    decorators share the same ``trace_id`` and are linked by ``parent_id``.

    Args:
        suite:       Logical grouping name (e.g. "invoice-agent").
        version:     Deployment version string (e.g. "v1", "2024-01-15").
        run_group:   Optional experiment label above version.
        commit_hash: Optional git commit SHA for CI integration.
        tags:        Arbitrary key-value metadata stored with the run.

    Returns:
        A decorator that wraps the target callable and returns its original
        return value unchanged.

    Usage::

        @trace(suite="my-agent", version="v2", tags={"env": "staging"})
        def call_llm(prompt):
            return model(prompt)
    """
    _tags = tags or {}

    def decorator(fn: Callable) -> Callable:
        if asyncio.iscoroutinefunction(fn):
            @functools.wraps(fn)
            async def async_wrapper(*args, **kwargs):
                return await _run_async(fn, args, kwargs, suite, version, run_group, commit_hash, _tags)
            return async_wrapper
        else:
            @functools.wraps(fn)
            def sync_wrapper(*args, **kwargs):
                return _run_sync(fn, args, kwargs, suite, version, run_group, commit_hash, _tags)
            return sync_wrapper

    return decorator


def _run_sync(fn, args, kwargs, suite, version, run_group, commit_hash, tags):
    stack = _get_stack()
    run_id = str(uuid4())

    if stack:
        parent_span = stack[-1]
        trace_id = parent_span["trace_id"]
        parent_id = parent_span["run_id"]
    else:
        trace_id = str(uuid4())
        parent_id = None

    span = {"run_id": run_id, "trace_id": trace_id}
    stack.append(span)

    input_value = _resolve_input(fn, args, kwargs)
    output_value = None
    status = "pass"
    token_count = None
    t0 = time.perf_counter()

    try:
        result = fn(*args, **kwargs)
        output_value = result
        token_count = _extract_token_count(result)
        return result
    except Exception as exc:
        status = "error"
        output_value = f"{type(exc).__name__}: {exc}"
        raise
    finally:
        latency_ms = (time.perf_counter() - t0) * 1000
        stack.pop()
        run = _build_run(
            run_id, trace_id, parent_id, suite, version, run_group, commit_hash,
            tags, input_value, output_value, status, latency_ms, token_count,
        )
        _safe_write(run)


async def _run_async(fn, args, kwargs, suite, version, run_group, commit_hash, tags):
    stack = _get_stack()
    run_id = str(uuid4())

    if stack:
        parent_span = stack[-1]
        trace_id = parent_span["trace_id"]
        parent_id = parent_span["run_id"]
    else:
        trace_id = str(uuid4())
        parent_id = None

    span = {"run_id": run_id, "trace_id": trace_id}
    stack.append(span)

    input_value = _resolve_input(fn, args, kwargs)
    output_value = None
    status = "pass"
    token_count = None
    t0 = time.perf_counter()

    try:
        result = await fn(*args, **kwargs)
        output_value = result
        token_count = _extract_token_count(result)
        return result
    except Exception as exc:
        status = "error"
        output_value = f"{type(exc).__name__}: {exc}"
        raise
    finally:
        latency_ms = (time.perf_counter() - t0) * 1000
        stack.pop()
        run = _build_run(
            run_id, trace_id, parent_id, suite, version, run_group, commit_hash,
            tags, input_value, output_value, status, latency_ms, token_count,
        )
        _safe_write(run)


def _resolve_input(fn: Callable, args: tuple, kwargs: dict) -> Any:
    """Build a structured representation of the call's input arguments."""
    try:
        sig = inspect.signature(fn)
        bound = sig.bind(*args, **kwargs)
        bound.apply_defaults()
        params = dict(bound.arguments)
        if len(params) == 1:
            return next(iter(params.values()))
        return params
    except Exception:
        if args and not kwargs:
            return args[0] if len(args) == 1 else list(args)
        return {"args": list(args), "kwargs": kwargs}


def _safe_write(run: Dict[str, Any]) -> None:
    """Write a run to storage, suppressing all exceptions."""
    try:
        from modelprobe.storage import router
        router.write_run(run)
    except Exception as exc:
        log.warning("modelprobe: failed to write run %s: %s", run.get("id"), exc)
