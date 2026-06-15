import pytest
from tests.conftest import NoOpBackend, CapturingBackend


@pytest.fixture
def noop_backend(monkeypatch):
    import modelprobe.storage.router as router_module
    backend = NoOpBackend()
    monkeypatch.setattr(router_module, "_backend", backend)
    yield backend
    monkeypatch.setattr(router_module, "_backend", None)


@pytest.fixture
def capturing_backend(monkeypatch):
    import modelprobe.storage.router as router_module
    backend = CapturingBackend()
    monkeypatch.setattr(router_module, "_backend", backend)
    yield backend
    monkeypatch.setattr(router_module, "_backend", None)
