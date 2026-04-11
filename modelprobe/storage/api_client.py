"""HTTP storage backend that forwards all operations to a remote ModelProbe server."""

from __future__ import annotations

import logging
import time
from typing import Any, Dict, List, Optional

log = logging.getLogger(__name__)

_DEFAULT_TIMEOUT = 10.0
_MAX_RETRIES = 3
_RETRY_BASE_S = 0.5


class APIClient:
    """Mirrors the SQLiteBackend interface, targeting a remote REST API.

    All requests are retried up to three times with exponential backoff.
    Timeouts default to 10 seconds.  Authentication is done via a Bearer
    token set in the MODELPROBE_API_KEY environment variable or config.

    Usage::

        client = APIClient(server="http://localhost:8000", api_key="secret")
        client.write_run({"id": "...", "suite": "my-agent", ...})
    """

    def __init__(self, server: str, api_key: Optional[str] = None) -> None:
        self._base = server.rstrip("/")
        self._headers: Dict[str, str] = {"Content-Type": "application/json"}
        if api_key:
            self._headers["Authorization"] = f"Bearer {api_key}"

    def _client(self):
        import httpx
        return httpx.Client(headers=self._headers, timeout=_DEFAULT_TIMEOUT)

    def _post(self, path: str, payload: Any) -> Any:
        return self._request("POST", path, json=payload)

    def _get(self, path: str, params: Optional[Dict[str, Any]] = None) -> Any:
        return self._request("GET", path, params=params)

    def _request(self, method: str, path: str, **kwargs) -> Any:
        url = f"{self._base}{path}"
        last_exc: Exception = RuntimeError("unreachable")

        for attempt in range(_MAX_RETRIES):
            try:
                with self._client() as client:
                    response = getattr(client, method.lower())(url, **kwargs)
                    response.raise_for_status()
                    return response.json()
            except Exception as exc:
                last_exc = exc
                if attempt < _MAX_RETRIES - 1:
                    sleep_s = _RETRY_BASE_S * (2 ** attempt)
                    log.debug("modelprobe api_client: retrying %s %s (attempt %d): %s", method, path, attempt + 1, exc)
                    time.sleep(sleep_s)

        raise last_exc

    def write_run(self, run: Dict[str, Any]) -> None:
        self._post("/api/runs", run)

    def get_run(self, run_id: str) -> Optional[Dict[str, Any]]:
        try:
            envelope = self._get(f"/api/runs/{run_id}")
            return envelope.get("data")
        except Exception:
            return None

    def list_runs(self, filters: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        params = {k: v for k, v in (filters or {}).items() if v is not None}
        envelope = self._get("/api/runs", params=params)
        return envelope.get("data", [])

    def write_eval_result(self, result: Dict[str, Any]) -> None:
        self._post("/api/eval-results", result)

    def write_test_case(self, tc: Dict[str, Any]) -> None:
        suite = tc["suite"]
        self._post(f"/api/suites/{suite}/test-cases", tc)

    def list_test_cases(self, suite: str) -> List[Dict[str, Any]]:
        envelope = self._get(f"/api/suites/{suite}/test-cases")
        return envelope.get("data", [])

    def list_eval_results(self, run_id: str) -> List[Dict[str, Any]]:
        envelope = self._get(f"/api/runs/{run_id}/eval-results")
        return envelope.get("data", [])

    def list_suites(self) -> List[str]:
        envelope = self._get("/api/suites")
        return [s["name"] for s in envelope.get("data", [])]
