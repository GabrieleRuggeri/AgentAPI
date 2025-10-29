"""Example agents used to demonstrate the API framework."""

from __future__ import annotations

import asyncio
from typing import Any, AsyncIterator, Dict, List


class EchoAgent:
    """Minimal agent implementation for demonstration purposes."""

    def __init__(self, prefix: str = "Echo") -> None:
        self.prefix = prefix

    async def invoke(self, input: str, conversation: List[Dict[str, Any]] | None = None, **_: Any) -> Dict[str, Any]:
        """Pretend to run a LangGraph workflow and return a response."""

        history = conversation or []
        text = f"{self.prefix}: {input}"
        return {
            "output": text,
            "metadata": {"turns": len(history) + 1, "prefix": self.prefix},
        }

    async def stream(self, input: str) -> AsyncIterator[Dict[str, Any]]:
        """Stream back characters from the input as individual events."""

        for index, token in enumerate(input.split()):
            await asyncio.sleep(0)  # demonstrate async generator
            yield {"event": "token", "data": token, "index": index}
        yield {"event": "final", "data": f"{self.prefix}: {input}"}


def create_agent(prefix: str = "Echo") -> EchoAgent:
    """Factory used in the configuration to instantiate the agent."""

    return EchoAgent(prefix=prefix)
