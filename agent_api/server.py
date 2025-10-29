"""FastAPI integration for exposing LangGraph agents."""

from __future__ import annotations

import inspect
import json
from collections.abc import AsyncIterable, Iterable
from typing import Any, Callable, Dict

from fastapi import Body, FastAPI, HTTPException
from fastapi.responses import JSONResponse, StreamingResponse
from pydantic import BaseModel

from .config import Config, RouteConfig, load_config


async def _invoke_callable(callable_obj: Callable[..., Any], **kwargs: Any) -> Any:
    result = callable_obj(**kwargs)
    if inspect.isawaitable(result):
        return await result  # type: ignore[return-value]
    return result


def _serialise_stream_item(item: Any) -> str:
    if hasattr(item, "model_dump"):
        payload = item.model_dump()
    elif isinstance(item, dict):
        payload = item
    else:
        payload = {"data": item}
    return f"data: {json.dumps(payload)}\n\n"


def _build_call_kwargs(route: RouteConfig, payload: Any) -> Dict[str, Any]:
    data: Dict[str, Any]
    if payload is None:
        data = {}
    elif hasattr(payload, "model_dump"):
        data = payload.model_dump()
    elif isinstance(payload, dict):
        data = payload
    else:
        raise HTTPException(400, detail="Unsupported payload type")

    kwargs: Dict[str, Any] = dict(route.constant_parameters)
    if route.parameter_mapping:
        missing = []
        for param, field in route.parameter_mapping.items():
            if field not in data:
                missing.append(field)
                continue
            kwargs[param] = data[field]
        if missing:
            raise HTTPException(
                status_code=422,
                detail=f"Missing required payload fields: {', '.join(missing)}",
            )
    else:
        kwargs.update(data)
    return kwargs


def _apply_response_model(
    route: RouteConfig, model_cls: type[BaseModel] | None, result: Any
) -> Any:
    if model_cls is None:
        return _wrap_non_model_response(route, result)
    if hasattr(result, "model_dump"):
        result_data = result.model_dump()
    elif isinstance(result, dict):
        result_data = result
    else:
        result_data = result
    model = model_cls.model_validate(result_data)
    payload = model.model_dump()
    if route.response_envelope:
        return {route.response_envelope: payload}
    return payload


def _wrap_non_model_response(route: RouteConfig, result: Any) -> Any:
    if route.response_envelope:
        return {route.response_envelope: result}
    return result


def _add_route(app: FastAPI, route: RouteConfig, agent: Any) -> None:
    request_model = route.load_request_model()
    response_model = route.load_response_model()
    agent_callable = getattr(agent, route.agent_method, None)
    if agent_callable is None:
        raise AttributeError(
            f"Configured agent method '{route.agent_method}' not found on agent"
        )

    async def handler(payload=Body(None)) -> Any:
        kwargs = _build_call_kwargs(route, payload)
        result = await _invoke_callable(agent_callable, **kwargs)

        if route.stream:
            if isinstance(result, (str, bytes)):
                iterable: Iterable[Any] | AsyncIterable[Any] = [result]
            elif isinstance(result, (AsyncIterable, Iterable)):
                iterable = result
            else:
                raise HTTPException(
                    500, detail="Stream routes must return an iterable or async iterable"
                )

            async def iterator():
                if isinstance(iterable, AsyncIterable):
                    async for item in iterable:
                        yield _serialise_stream_item(item)
                else:
                    for item in iterable:
                        yield _serialise_stream_item(item)
                yield "data: {\"event\": \"end\"}\n\n"

            return StreamingResponse(iterator(), media_type=route.stream_media_type)

        payload_out = _apply_response_model(route, response_model, result)
        return JSONResponse(payload_out)

    if request_model is not None:
        handler.__annotations__["payload"] = request_model  # type: ignore[index]
    else:
        handler.__annotations__["payload"] = Dict[str, Any] | None  # type: ignore[index]

    app.add_api_route(
        route.path,
        handler,
        name=route.name,
        methods=[route.method],
        summary=route.summary,
        description=route.description,
        response_model=None,
    )


def create_app(config: Config | None = None, agent: Any | None = None) -> FastAPI:
    """Factory used by Uvicorn to create the FastAPI app."""

    config = config or load_config()
    agent_instance = agent or config.agent.create_agent()

    app = FastAPI(
        title=config.app.title,
        version=config.app.version,
        description=config.app.description,
        docs_url=config.app.docs_url,
        openapi_url=config.app.openapi_url,
        root_path=config.app.root_path,
    )

    @app.get("/health", tags=["system"], summary="Health check")
    async def health() -> Dict[str, str]:
        return {"status": "ok"}

    for route in config.routes:
        _add_route(app, route, agent_instance)

    return app
