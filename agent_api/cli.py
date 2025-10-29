"""Command-line interface for running the Agent API server."""

from __future__ import annotations

import argparse
import os

import uvicorn

from .config import load_config
from .server import create_app


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run a LangGraph agent as an API")
    parser.add_argument(
        "--config",
        help=(
            "Path to the YAML configuration file. Overrides the AGENT_API_CONFIG environment variable."
        ),
    )
    parser.add_argument(
        "--host",
        default=os.getenv("AGENT_API_HOST", "0.0.0.0"),
        help="Host interface for the server",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=int(os.getenv("AGENT_API_PORT", "8000")),
        help="Port to bind the HTTP server",
    )
    return parser


def main(argv: list[str] | None = None) -> None:
    parser = build_parser()
    args = parser.parse_args(argv)

    config = load_config(args.config) if args.config else None
    app = create_app(config=config)

    uvicorn.run(app, host=args.host, port=args.port)


__all__ = ["build_parser", "main"]
