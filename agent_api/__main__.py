"""Allows ``python -m agent_api`` to run the CLI."""

from .cli import main


if __name__ == "__main__":  # pragma: no cover - thin wrapper
    main()
