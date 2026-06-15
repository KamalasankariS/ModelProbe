"""Unit tests for the configuration ladder."""

import os
import pytest

from modelprobe.config import Settings


class TestSettingsDefaults:
    def test_default_mode_is_local(self):
        s = Settings()
        assert s.mode == "local"

    def test_default_db_path_is_set(self):
        s = Settings()
        assert "modelprobe.db" in s.db_path

    def test_default_llm_endpoint(self):
        s = Settings()
        assert "openai" in s.llm_endpoint

    def test_default_cors_origins(self):
        s = Settings()
        assert s.cors_origins == ["*"]

    def test_api_key_defaults_none(self):
        s = Settings()
        assert s.api_key is None


class TestSettingsOverrides:
    def test_programmatic_override(self):
        s = Settings(overrides={"server": "http://example.com"})
        assert s.server == "http://example.com"
        assert s.mode == "remote"

    def test_update_changes_values(self):
        s = Settings()
        assert s.mode == "local"
        s.update(server="http://example.com")
        assert s.mode == "remote"

    def test_none_overrides_are_ignored(self):
        s = Settings(overrides={"server": None})
        assert s.server is None
        assert s.mode == "local"


class TestSettingsEnvVars:
    def test_env_var_server(self, monkeypatch):
        monkeypatch.setenv("MODELPROBE_SERVER", "http://env-server.com")
        s = Settings()
        assert s.server == "http://env-server.com"
        assert s.mode == "remote"

    def test_env_var_db_path(self, monkeypatch):
        monkeypatch.setenv("MODELPROBE_DB_PATH", "/tmp/custom.db")
        s = Settings()
        assert s.db_path == "/tmp/custom.db"

    def test_env_var_cors_origins_split(self, monkeypatch):
        monkeypatch.setenv("MODELPROBE_CORS_ORIGINS", "http://a.com, http://b.com")
        s = Settings()
        assert s.cors_origins == ["http://a.com", "http://b.com"]


class TestSettingsAsDict:
    def test_secrets_are_masked(self):
        s = Settings(overrides={"api_key": "secret123", "llm_api_key": "secret456"})
        d = s.as_dict()
        assert d["api_key"] == "***"
        assert d["llm_api_key"] == "***"

    def test_non_secrets_are_visible(self):
        s = Settings()
        d = s.as_dict()
        assert "modelprobe.db" in d["db_path"]
