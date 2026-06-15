"""Unit tests for the storage router delegation logic."""

import pytest
import modelprobe.storage.router as router_module
from tests.conftest import CapturingBackend


@pytest.fixture(autouse=True)
def isolate_backend(monkeypatch):
    monkeypatch.setattr(router_module, "_backend", None)
    yield
    monkeypatch.setattr(router_module, "_backend", None)


class TestRouterDelegation:
    def test_write_run_delegates_to_backend(self, monkeypatch):
        backend = CapturingBackend()
        monkeypatch.setattr(router_module, "_backend", backend)
        router_module.write_run({"id": "r1", "trace_id": "t1", "suite": "s", "version": "v1"})
        assert len(backend.runs) == 1

    def test_write_eval_result_delegates(self, monkeypatch):
        backend = CapturingBackend()
        monkeypatch.setattr(router_module, "_backend", backend)
        router_module.write_eval_result({"run_id": "r1", "test_case_id": "tc1"})
        assert len(backend.eval_results) == 1

    def test_list_runs_delegates(self, monkeypatch):
        backend = CapturingBackend()
        backend.runs.append({"id": "r1", "suite": "s"})
        monkeypatch.setattr(router_module, "_backend", backend)
        runs = router_module.list_runs()
        assert len(runs) == 1

    def test_backend_error_does_not_propagate(self, monkeypatch):
        class BrokenBackend:
            def write_run(self, run):
                raise RuntimeError("db exploded")
        monkeypatch.setattr(router_module, "_backend", BrokenBackend())
        router_module.write_run({"id": "r1"})  # should not raise


class TestResetBackend:
    def test_reset_clears_backend(self, monkeypatch):
        backend = CapturingBackend()
        monkeypatch.setattr(router_module, "_backend", backend)
        assert router_module._backend is not None
        router_module.reset_backend()
        assert router_module._backend is None
