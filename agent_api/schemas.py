"""Common Pydantic schemas used when building agent APIs."""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class Message(BaseModel):
    """Represents a single message exchanged with the agent."""

    role: str = Field(description="Role of the message sender, e.g. 'user' or 'assistant'")
    content: str = Field(description="Natural language content of the message")


class InvokeRequest(BaseModel):
    """Default payload for invoking an agent."""

    input: str = Field(..., description="The input prompt to send to the agent")
    conversation: List[Message] | None = Field(
        default=None,
        description="Optional previous messages to give the agent conversational context",
    )
    config: Dict[str, Any] | None = Field(
        default=None,
        description="Optional configuration overrides passed directly to the agent",
    )


class InvokeResponse(BaseModel):
    """Default response model wrapping agent outputs."""

    output: Any
    metadata: Dict[str, Any] | None = None


class StreamChunk(BaseModel):
    """Chunk emitted when streaming from the agent."""

    event: str = Field(description="Type of event, e.g. 'token' or 'final'")
    data: Dict[str, Any]
