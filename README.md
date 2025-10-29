# LangGraph Agent API Framework

The Agent API framework turns any LangGraph-compatible agent into a fully documented HTTP API powered by FastAPI. Every detail of the server—from the agent factory to the exposed routes—is configured through declarative YAML so you can publish new APIs without writing bespoke glue code.

## Why this framework?

- 🔌 **Dynamic agent wiring** – map agent methods onto HTTP endpoints through configuration.
- 📦 **Pydantic validation** – reuse or define request/response models for robust payload handling.
- 🌊 **Streaming support** – expose async generators or iterables as Server-Sent Events (SSE).
- 📖 **First-class documentation** – Swagger UI and OpenAPI endpoints are configurable per deployment.
- ⚙️ **Environment aware** – select the active configuration via `AGENT_API_CONFIG`.

## 1. Set up the project

1. Create and activate a virtual environment. The commands below use the
   [`uv`](https://github.com/astral-sh/uv) package manager, but a standard
   `python -m venv` workflow works just as well.

   ```bash
   uv venv
   source .venv/bin/activate
   ```

2. Install the framework and development tooling (includes pytest and HTTPX for
   testing).

   ```bash
   uv pip install -e .[dev]
   # or: pip install -e .[dev]
   ```

## 2. Describe your API

Define the API in YAML. The repository ships with [`agent_api.yaml`](./agent_api.yaml) which exposes an example `EchoAgent`:

```yaml
app:
  title: "Echo Agent API"
  version: "0.1.0"
  description: "Example API generated from a LangGraph style agent"
  docs_url: "/docs"
  openapi_url: "/openapi.json"

agent:
  import_path: "examples.agents:create_agent"
  init_kwargs:
    prefix: "Echo"

routes:
  - name: invoke
    path: /invoke
    method: POST
    summary: "Invoke the agent synchronously"
    description: "Calls the agent's invoke method with the provided payload."
    agent_method: invoke
    request_model: "agent_api.schemas.InvokeRequest"
    response_model: "agent_api.schemas.InvokeResponse"
    parameter_mapping:
      input: input
      conversation: conversation
      config: config
    response_envelope: result

  - name: stream
    path: /stream
    method: POST
    summary: "Stream tokens from the agent"
    description: "Streams incremental events from the agent's stream method."
    agent_method: stream
    request_model: "agent_api.schemas.InvokeRequest"
    parameter_mapping:
      input: input
    stream: true
    stream_media_type: text/event-stream
```

- `app` metadata configures the FastAPI title, version, description, and documentation endpoints. Keep `docs_url` and `openapi_url` set to serve Swagger UI and the OpenAPI schema; set either to `null` to disable it.
- `agent` describes how to instantiate your agent. `import_path` can reference a class or factory, and `init_kwargs` are passed directly during construction.
- `routes` define the HTTP surface area. Map the HTTP method, path, and request/response models to specific agent methods. The example demonstrates synchronous and streaming endpoints.

## 3. Provide Pydantic models

Schemas for the example configuration are available in [`agent_api/schemas.py`](./agent_api/schemas.py). Add your own models to your project and reference them via import strings in the YAML file so requests and responses are validated automatically.

## 4. Run the API server

Start Uvicorn with the provided application factory:

```bash
uvicorn agent_api.server:create_app --reload
```

The server automatically loads configuration from `agent_api.yaml` (or the path indicated by `AGENT_API_CONFIG`) and registers every configured route. Swagger UI is served at `http://localhost:8000/docs` and the OpenAPI schema at `http://localhost:8000/openapi.json` when these URLs are enabled in the configuration.

## 5. Exercise the endpoints

Run your first requests against the live server:

```bash
# Synchronous invocation
curl -X POST http://localhost:8000/invoke \
  -H "Content-Type: application/json" \
  -d '{"input": "Hello from LangGraph!"}'

# Streaming responses via SSE
curl -N -X POST http://localhost:8000/stream \
  -H "Content-Type: application/json" \
  -d '{"input": "Streaming makes it easy"}'
```

## 6. Install as a dependency

Use the framework from another project by declaring it as a dependency. The
distribution name is `agent-api`, and it exposes the importable package
`agent_api`:

```bash
uv add agent-api
# or: pip install agent-api
```

After installation the console script `agent-api` becomes available, mirroring
the CLI provided in this repository. You can also embed the FastAPI app
directly, as shown in the next section.

## Configuration reference

### Environment variables

- `AGENT_API_CONFIG`: Override the configuration file path. When omitted the loader searches for `agent_api.yaml`, `agent-api.yaml`, or `config/agent_api.yaml` in the current directory.

### YAML options

`app`

- `title`, `version`, `description`: Metadata surfaced through Swagger and OpenAPI.
- `docs_url`: URL path serving the interactive documentation. Set to `null` to disable Swagger UI entirely.
- `openapi_url`: URL path serving the OpenAPI document. Set to `null` to disable schema generation.
- `root_path`: FastAPI root path (useful behind reverse proxies).

`agent`

- `import_path`: Import string targeting the agent class or a factory callable (e.g. `package.module:callable`).
- `init_kwargs`: Keyword arguments forwarded during agent instantiation.

`routes`

- `name`: Name applied to the FastAPI route.
- `path`: HTTP path exposed by the API.
- `method`: HTTP verb (`GET`, `POST`, `PUT`, `PATCH`, `DELETE`). Defaults to `POST`.
- `summary` / `description`: Human-readable documentation shown in Swagger UI.
- `agent_method`: Method name on the agent instance that is executed when the route is called.
- `request_model`: Optional import string referencing a Pydantic `BaseModel` used to validate the request body.
- `response_model`: Optional import string referencing a Pydantic `BaseModel` used to validate the response.
- `parameter_mapping`: Mapping from agent argument name to request field. When omitted the full payload is expanded into keyword arguments.
- `constant_parameters`: Extra keyword arguments injected into every invocation.
- `stream`: When `true`, the method must return an iterable or async iterable which will be streamed to the client as SSE.
- `stream_media_type`: MIME type for streaming responses (`text/event-stream` by default).
- `response_envelope`: Wrap the response inside an outer object (e.g. `{ "result": ... }`).

## Programmatic embedding

Create an application instance manually when embedding within another service:

```python
from pathlib import Path

from agent_api.config import Config
from agent_api.server import create_app
from examples.agents import create_agent
import yaml

config_data = yaml.safe_load(Path("agent_api.yaml").read_text())
config = Config.from_mapping(config_data)
agent = create_agent(prefix="Echo")
app = create_app(config=config, agent=agent)
```

## Testing and quality checks

Run the automated test suite and bytecode compilation check before shipping changes:

```bash
pytest
python -m compileall agent_api examples main.py
```

## License

MIT
