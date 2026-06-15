"""Unit test fixtures — isolated backends for all unit tests."""

import pytest
from tests.conftest import NoOpBackend, CapturingBackend


@pytest.fixture
def noop_backend(monkeypatch):
    """Inject a no-op backend so storage writes are discarded."""
    import modelprobe.storage.router as router_module
    backend = NoOpBackend()
    monkeypatch.setattr(router_module, "_backend", backend)
    yield backend
    monkeypatch.setattr(router_module, "_backend", None)


@pytest.fixture
def capturing_backend(monkeypatch):
    """Inject a capturing backend to inspect what was written."""
    import modelprobe.storage.router as router_module
    backend = CapturingBackend()
    monkeypatch.setattr(router_module, "_backend", backend)
    yield backend
    monkeypatch.setattr(router_module, "_backend", None)
