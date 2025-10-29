import pytest
from fastapi.testclient import TestClient

from agent_api.config import AgentConfig, AppConfig, Config, RouteConfig
from agent_api.server import create_app
from examples.agents import create_agent


@pytest.fixture()
def sample_config() -> Config:
    return Config(
        app=AppConfig(
            title="Test Agent API",
            description="Integration tests for the agent API",
            docs_url="/docs",
            openapi_url="/openapi.json",
        ),
        agent=AgentConfig(import_path="examples.agents:create_agent", init_kwargs={"prefix": "Test"}),
        routes=[
            RouteConfig(
                name="invoke",
                path="/invoke",
                method="POST",
                summary="Invoke the agent synchronously",
                agent_method="invoke",
                request_model="agent_api.schemas.InvokeRequest",
                response_model="agent_api.schemas.InvokeResponse",
                parameter_mapping={
                    "input": "input",
                    "conversation": "conversation",
                    "config": "config",
                },
                response_envelope="result",
            ),
            RouteConfig(
                name="stream",
                path="/stream",
                method="POST",
                summary="Stream tokens from the agent",
                agent_method="stream",
                request_model="agent_api.schemas.InvokeRequest",
                parameter_mapping={"input": "input"},
                stream=True,
            ),
        ],
    )


def test_invoke_endpoint_returns_enveloped_response(sample_config: Config) -> None:
    app = create_app(config=sample_config, agent=create_agent(prefix="Test"))

    client = TestClient(app)
    payload = {
        "input": "ping",
        "conversation": [{"role": "user", "content": "ping"}],
        "config": {"temperature": 0.1},
    }
    response = client.post("/invoke", json=payload)

    assert response.status_code == 200
    body = response.json()
    assert body["result"]["output"] == "Test: ping"
    assert body["result"]["metadata"]["turns"] == 2
    assert body["result"]["metadata"]["prefix"] == "Test"


def test_stream_endpoint_emits_server_sent_events(sample_config: Config) -> None:
    app = create_app(config=sample_config, agent=create_agent(prefix="Test"))

    client = TestClient(app)
    with client.stream("POST", "/stream", json={"input": "hello world"}) as response:
        assert response.status_code == 200
        assert response.headers["content-type"].startswith("text/event-stream")
        body = "".join(response.iter_text())

    events = [line for line in body.strip().split("\n\n") if line]
    assert any("\"final\"" in event for event in events)
    assert events[-1] == "data: {\"event\": \"end\"}"


def test_swagger_ui_is_enabled(sample_config: Config) -> None:
    app = create_app(config=sample_config, agent=create_agent(prefix="Test"))

    client = TestClient(app)
    docs_response = client.get("/docs")
    openapi_response = client.get("/openapi.json")

    assert docs_response.status_code == 200
    assert "Swagger UI" in docs_response.text

    assert openapi_response.status_code == 200
    schema = openapi_response.json()
    assert schema["info"]["title"] == "Test Agent API"
    assert schema["paths"]
