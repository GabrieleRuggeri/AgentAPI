"""Configuration models for the Agent API framework."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any, Dict, Iterable, List, Literal

from dotenv import load_dotenv
from pydantic import BaseModel, Field, ValidationError, field_validator
import yaml

from .importing import ImportString, load_object

HttpMethod = Literal["GET", "POST", "PUT", "PATCH", "DELETE"]


class AppConfig(BaseModel):
    """Settings that describe the FastAPI application."""

    title: str = "LangGraph Agent API"
    version: str = "0.1.0"
    description: str | None = None
    docs_url: str | None = "/docs"
    openapi_url: str | None = "/openapi.json"
    root_path: str = ""


class AgentConfig(BaseModel):
    """Configuration for instantiating the agent."""

    import_path: str = Field(
        ..., description="Import string pointing to the agent class or factory"
    )
    init_kwargs: Dict[str, Any] = Field(
        default_factory=dict,
        description="Keyword arguments passed when constructing the agent",
    )

    def create_agent(self) -> Any:
        """Instantiate the configured agent."""

        factory = ImportString(self.import_path).load_callable()
        return factory(**self.init_kwargs)


class RouteConfig(BaseModel):
    """Definition of a single HTTP endpoint that calls into the agent."""

    name: str
    path: str
    method: HttpMethod = "POST"
    summary: str | None = None
    description: str | None = None
    agent_method: str = Field(
        ..., description="Name of the method on the agent to execute"
    )
    request_model: str | None = Field(
        default=None,
        description=(
            "Import string pointing to a Pydantic model used to validate the request body"
        ),
    )
    response_model: str | None = Field(
        default=None,
        description=(
            "Import string pointing to a Pydantic model used to validate the response"
        ),
    )
    parameter_mapping: Dict[str, str] = Field(
        default_factory=dict,
        description=(
            "Mapping from agent function parameter names to fields on the request model"
        ),
    )
    constant_parameters: Dict[str, Any] = Field(
        default_factory=dict,
        description="Extra parameters always passed to the agent method",
    )
    stream: bool = Field(
        default=False, description="Whether the agent method returns a stream"
    )
    stream_media_type: str = Field(
        default="text/event-stream",
        description="Media type used when streaming responses",
    )
    response_envelope: str | None = Field(
        default=None,
        description=(
            "If provided, the agent result will be returned inside a dict under this key"
        ),
    )

    @field_validator("parameter_mapping", mode="before")
    @classmethod
    def _validate_mapping(cls, value: Any) -> Dict[str, str]:
        if value is None:
            return {}
        if isinstance(value, dict):
            return {str(k): str(v) for k, v in value.items()}
        msg = "parameter_mapping must be a mapping of agent parameter -> payload field"
        raise TypeError(msg)

    def load_request_model(self) -> type[BaseModel] | None:
        if not self.request_model:
            return None
        model = load_object(self.request_model)
        if not isinstance(model, type) or not issubclass(model, BaseModel):
            msg = f"Request model '{self.request_model}' is not a Pydantic BaseModel"
            raise TypeError(msg)
        return model

    def load_response_model(self) -> type[BaseModel] | None:
        if not self.response_model:
            return None
        model = load_object(self.response_model)
        if not isinstance(model, type) or not issubclass(model, BaseModel):
            msg = f"Response model '{self.response_model}' is not a Pydantic BaseModel"
            raise TypeError(msg)
        return model


class Config(BaseModel):
    """Root configuration for the API server."""

    app: AppConfig = Field(default_factory=AppConfig)
    agent: AgentConfig
    routes: List[RouteConfig]

    @classmethod
    def from_mapping(cls, data: Dict[str, Any]) -> "Config":
        try:
            return cls.model_validate(data)
        except ValidationError as exc:
            raise ValueError("Invalid agent API configuration") from exc


DEFAULT_CONFIG_FILENAMES: Iterable[str] = (
    "agent_api.yaml",
    "agent-api.yaml",
    "config/agent_api.yaml",
)


def _resolve_config_path(explicit: str | None) -> Path:
    if explicit:
        path = Path(explicit).expanduser()
        if not path.exists():
            msg = f"Configuration file not found at '{path}'"
            raise FileNotFoundError(msg)
        return path

    for candidate in DEFAULT_CONFIG_FILENAMES:
        path = Path(candidate)
        if path.exists():
            return path
    raise FileNotFoundError(
        "No configuration file found. Provide AGENT_API_CONFIG or create agent_api.yaml"
    )


def load_config(path: str | Path | None = None) -> Config:
    """Load configuration from YAML, respecting the AGENT_API_CONFIG environment variable."""

    load_dotenv()
    env_path = Path(path) if path else None
    if env_path is None:
        env_value = os.getenv("AGENT_API_CONFIG")
        env_path = Path(env_value).expanduser() if env_value else None
    target_path = _resolve_config_path(str(env_path) if env_path else None)
    with target_path.open("r", encoding="utf-8") as stream:
        data = yaml.safe_load(stream) or {}
    return Config.from_mapping(data)
