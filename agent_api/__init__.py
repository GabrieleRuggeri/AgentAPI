"""Agent API framework."""

from __future__ import annotations

from importlib.metadata import version, PackageNotFoundError

from .config import AgentConfig, AppConfig, Config, RouteConfig, load_config
from .server import create_app

try:
    __version__ = version("agent-api")
except PackageNotFoundError:  # pragma: no cover - during local development
    __version__ = "0.0.0"

__all__ = [
    "AgentConfig",
    "AppConfig",
    "Config",
    "RouteConfig",
    "create_app",
    "load_config",
    "__version__",
]
