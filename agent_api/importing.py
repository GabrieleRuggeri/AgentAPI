"""Utilities for dynamic imports used by the Agent API framework."""

from __future__ import annotations

import importlib
from dataclasses import dataclass
from functools import reduce
from typing import Any, Callable


class ImportErrorMessage(RuntimeError):
    """Raised when an import string cannot be resolved."""


@dataclass(frozen=True)
class ImportString:
    """Representation of an import string.

    The import string is expected in the ``"module.submodule:attribute"`` form.
    The attribute part may contain dots for nested attributes.
    """

    value: str

    def load(self) -> Any:
        """Return the object pointed to by the import string."""

        module_path, attribute = self._split()
        module = importlib.import_module(module_path)
        return reduce(getattr, attribute.split("."), module)

    def load_callable(self) -> Callable[..., Any]:
        """Return a callable referenced by the import string."""

        obj = self.load()
        if not callable(obj):
            msg = f"Imported object '{self.value}' is not callable"
            raise ImportErrorMessage(msg)
        return obj

    def _split(self) -> tuple[str, str]:
        if ":" not in self.value:
            msg = (
                "Import strings must be in 'module.submodule:attribute' form; "
                f"got '{self.value}'"
            )
            raise ImportErrorMessage(msg)
        module_path, attribute = self.value.split(":", 1)
        return module_path, attribute


def load_object(path: str) -> Any:
    """Helper to load any object using an import string."""

    return ImportString(path).load()


def load_callable(path: str) -> Callable[..., Any]:
    """Helper to load a callable using an import string."""

    return ImportString(path).load_callable()
