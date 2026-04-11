"""
ModelProbe configuration ladder.

Priority (lowest to highest):
  1. Hardcoded defaults
  2. ~/.modelprobe/config.toml  (optional)
  3. Environment variables
  4. modelprobe.configure(**kwargs)  (programmatic — highest priority)

Usage::

    from modelprobe.config import settings, configure

    # Read a value
    print(settings.mode)  # "local" | "remote"

    # Override programmatically
    configure(server="http://localhost:8000")
"""

from __future__ import annotations

import os
import threading
from pathlib import Path
from typing import Any, Dict, Optional

# ---------------------------------------------------------------------------
# Internal singleton state — NOT initialised on import
# ---------------------------------------------------------------------------

_lock = threading.Lock()
_settings: Optional["Settings"] = None


class Settings:
    """Holds all resolved configuration for a ModelProbe session.

    Attributes are resolved once (lazily) and cached for the process lifetime
    unless ``configure()`` is called again.
    """

    # ------------------------------------------------------------------
    # Defaults
    # ------------------------------------------------------------------
    _DEFAULTS: Dict[str, Any] = {
        "server": None,
        "db_path": str(Path.home() / ".modelprobe" / "modelprobe.db"),
        "api_key": None,
        "llm_endpoint": "https://api.openai.com/v1/chat/completions",
        "llm_api_key": None,
        "cors_origins": ["*"],
        "log_level": "WARNING",
    }

    def __init__(self, overrides: Optional[Dict[str, Any]] = None) -> None:
        self._values: Dict[str, Any] = dict(self._DEFAULTS)
        self._load_toml()
        self._load_env()
        if overrides:
            self._values.update({k: v for k, v in overrides.items() if v is not None})

    # ------------------------------------------------------------------
    # Loaders
    # ------------------------------------------------------------------

    def _load_toml(self) -> None:
        """Merge ~/.modelprobe/config.toml if it exists."""
        toml_path = Path.home() / ".modelprobe" / "config.toml"
        if not toml_path.exists():
            return
        try:
            # Python 3.11+ ships tomllib; older versions may have tomli installed
            try:
                import tomllib  # type: ignore[import]
            except ImportError:
                try:
                    import tomli as tomllib  # type: ignore[import,no-redef]
                except ImportError:
                    return  # No TOML parser available — skip silently
            with open(toml_path, "rb") as f:
                data = tomllib.load(f)
            for key, value in data.items():
                if key in self._values:
                    self._values[key] = value
        except Exception:
            pass  # Corrupt or unreadable config — use defaults

    def _load_env(self) -> None:
        """Merge environment variables (MODELPROBE_* prefix)."""
        mapping = {
            "MODELPROBE_SERVER": "server",
            "MODELPROBE_DB_PATH": "db_path",
            "MODELPROBE_API_KEY": "api_key",
            "MODELPROBE_LLM_ENDPOINT": "llm_endpoint",
            "MODELPROBE_LLM_API_KEY": "llm_api_key",
            "MODELPROBE_CORS_ORIGINS": "cors_origins",
            "MODELPROBE_LOG_LEVEL": "log_level",
        }
        for env_var, key in mapping.items():
            val = os.environ.get(env_var)
            if val is not None:
                if key == "cors_origins":
                    self._values[key] = [o.strip() for o in val.split(",")]
                else:
                    self._values[key] = val

    # ------------------------------------------------------------------
    # Property accessors
    # ------------------------------------------------------------------

    @property
    def server(self) -> Optional[str]:
        """Remote server URL, or None for local SQLite mode."""
        return self._values.get("server")

    @property
    def db_path(self) -> str:
        """Absolute path to the local SQLite database file."""
        return self._values["db_path"]

    @property
    def api_key(self) -> Optional[str]:
        """API key for authenticating against a remote ModelProbe server."""
        return self._values.get("api_key")

    @property
    def llm_endpoint(self) -> str:
        """OpenAI-compatible endpoint used by the llm_judge evaluator."""
        return self._values["llm_endpoint"]

    @property
    def llm_api_key(self) -> Optional[str]:
        """API key for the LLM endpoint (llm_judge evaluator)."""
        return self._values.get("llm_api_key")

    @property
    def cors_origins(self) -> list:
        """List of allowed CORS origins for the server."""
        return self._values["cors_origins"]

    @property
    def log_level(self) -> str:
        """Python logging level string."""
        return self._values["log_level"]

    @property
    def mode(self) -> str:
        """'remote' if a server URL is configured, otherwise 'local'."""
        return "remote" if self.server else "local"

    def update(self, **kwargs: Any) -> None:
        """Apply programmatic overrides (highest priority)."""
        self._values.update({k: v for k, v in kwargs.items() if v is not None})

    def as_dict(self) -> Dict[str, Any]:
        """Return a copy of the resolved settings dict (safe to print)."""
        safe = dict(self._values)
        for secret_key in ("api_key", "llm_api_key"):
            if safe.get(secret_key):
                safe[secret_key] = "***"
        return safe


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def _get_settings() -> Settings:
    """Return the (lazily initialised) settings singleton."""
    global _settings
    if _settings is None:
        with _lock:
            if _settings is None:
                _settings = Settings()
    return _settings


# Module-level proxy — attribute access delegates to the singleton
class _SettingsProxy:
    """Transparent proxy to the Settings singleton.

    Allows ``from modelprobe.config import settings`` to work before the
    singleton is initialised, while still deferring all I/O to first access.
    """

    def __getattr__(self, name: str) -> Any:
        return getattr(_get_settings(), name)

    def __repr__(self) -> str:  # pragma: no cover
        return repr(_get_settings().as_dict())


settings: Settings = _SettingsProxy()  # type: ignore[assignment]


def configure(
    *,
    server: Optional[str] = None,
    db_path: Optional[str] = None,
    api_key: Optional[str] = None,
    llm_endpoint: Optional[str] = None,
    llm_api_key: Optional[str] = None,
    cors_origins: Optional[list] = None,
    log_level: Optional[str] = None,
) -> None:
    """Override ModelProbe settings programmatically.

    This is the highest-priority configuration source — it overrides env vars,
    TOML config, and all defaults.  Safe to call at any point after import.

    Usage::

        import modelprobe
        modelprobe.configure(server="http://localhost:8000")
        # All subsequent SDK calls route to the remote server
    """
    global _settings
    with _lock:
        s = _get_settings()
        kwargs = {
            "server": server,
            "db_path": db_path,
            "api_key": api_key,
            "llm_endpoint": llm_endpoint,
            "llm_api_key": llm_api_key,
            "cors_origins": cors_origins,
            "log_level": log_level,
        }
        s.update(**kwargs)
