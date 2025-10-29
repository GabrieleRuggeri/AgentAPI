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

    The import string is expected in the ``"module.submodule:attribute"`` form by
    default, but ``"module.submodule.attribute"`` is also accepted for
    convenience. The attribute part may contain dots for nested attributes.
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
        if ":" in self.value:
            module_path, attribute = self.value.split(":", 1)
            if not module_path or not attribute:
                msg = (
                    "Import strings must include both module and attribute parts; "
                    f"got '{self.value}'"
                )
                raise ImportErrorMessage(msg)
            return module_path, attribute

        if "." not in self.value:
            msg = (
                "Import strings must include a module path and attribute separated "
                f"by ':' or '.'; got '{self.value}'"
            )
            raise ImportErrorMessage(msg)

        module_path, attribute = self.value.rsplit(".", 1)
        if not module_path or not attribute:
            msg = (
                "Import strings must include both module and attribute parts; "
                f"got '{self.value}'"
            )
            raise ImportErrorMessage(msg)
        return module_path, attribute


def load_object(path: str) -> Any:
    """Helper to load any object using an import string."""

    return ImportString(path).load()


def load_callable(path: str) -> Callable[..., Any]:
    """Helper to load a callable using an import string."""

    return ImportString(path).load_callable()
