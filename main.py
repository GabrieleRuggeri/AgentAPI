"""Command line entry point maintained for backwards compatibility."""

from agent_api.cli import main

__all__ = ["main"]

if __name__ == "__main__":
    main()
