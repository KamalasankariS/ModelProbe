"""Storage router — delegates to SQLiteBackend or APIClient based on config."""

from __future__ import annotations

import logging
import threading
from typing import Any, Dict, List, Optional

log = logging.getLogger(__name__)

_lock = threading.Lock()
_backend = None


def _get_backend():
    """Return the initialised storage backend, creating it on first call."""
    global _backend
    if _backend is None:
        with _lock:
            if _backend is None:
                _backend = _create_backend()
    return _backend


def _create_backend():
    from modelprobe.config import settings

    if settings.mode == "remote":
        from modelprobe.storage.api_client import APIClient
        return APIClient(
            server=settings.server,
            api_key=settings.api_key,
        )
    else:
        from modelprobe.storage.sqlite import SQLiteBackend
        return SQLiteBackend(db_path=settings.db_path)


def reset_backend() -> None:
    """Force the router to re-initialise the backend on next access.

    Called internally after ``configure()`` changes the storage mode.
    """
    global _backend
    with _lock:
        _backend = None


def write_run(run: Dict[str, Any]) -> None:
    """Persist a run record to the configured backend.

    Usage::

        write_run({"id": "...", "trace_id": "...", "suite": "my-agent", ...})
    """
    try:
        _get_backend().write_run(run)
    except Exception as exc:
        log.warning("modelprobe: storage write_run failed: %s", exc)


def get_run(run_id: str) -> Optional[Dict[str, Any]]:
    """Fetch a single run by ID, including nested steps.

    Usage::

        run = get_run("abc-123")
    """
    try:
        return _get_backend().get_run(run_id)
    except Exception as exc:
        log.warning("modelprobe: storage get_run failed: %s", exc)
        return None


def list_runs(filters: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
    """List runs with optional filters.

    Supported filter keys: suite, version, run_group, status, date_from,
    date_to, tag (formatted as "key:value").

    Usage::

        runs = list_runs({"suite": "my-agent", "status": "fail"})
    """
    try:
        return _get_backend().list_runs(filters or {})
    except Exception as exc:
        log.warning("modelprobe: storage list_runs failed: %s", exc)
        return []


def write_eval_result(result: Dict[str, Any]) -> None:
    """Persist an EvalResult record.

    Usage::

        write_eval_result({"run_id": "...", "test_case_id": "tc_001", ...})
    """
    try:
        _get_backend().write_eval_result(result)
    except Exception as exc:
        log.warning("modelprobe: storage write_eval_result failed: %s", exc)


def write_test_case(tc: Dict[str, Any]) -> None:
    """Persist a TestCase record.

    Usage::

        write_test_case({"suite": "my-agent", "test_case_id": "tc_001", ...})
    """
    try:
        _get_backend().write_test_case(tc)
    except Exception as exc:
        log.warning("modelprobe: storage write_test_case failed: %s", exc)


def list_test_cases(suite: str) -> List[Dict[str, Any]]:
    """Return all test cases for a given suite.

    Usage::

        cases = list_test_cases("my-agent")
    """
    try:
        return _get_backend().list_test_cases(suite)
    except Exception as exc:
        log.warning("modelprobe: storage list_test_cases failed: %s", exc)
        return []


def list_eval_results(run_id: str) -> List[Dict[str, Any]]:
    """Return all eval results for a given run.

    Usage::

        results = list_eval_results("abc-123")
    """
    try:
        return _get_backend().list_eval_results(run_id)
    except Exception as exc:
        log.warning("modelprobe: storage list_eval_results failed: %s", exc)
        return []


def list_suites() -> List[str]:
    """Return distinct suite names recorded in storage.

    Usage::

        suites = list_suites()
    """
    try:
        return _get_backend().list_suites()
    except Exception as exc:
        log.warning("modelprobe: storage list_suites failed: %s", exc)
        return []
