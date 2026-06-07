# AI Agent Guidelines for mAI-consigliere

This document provides essential information for AI coding agents working in this repository.

## Project Overview

**mAI-consigliere** is an agentic AI system comprising an orchestrator agent (the "mAI Consigliere") and multiple specialized expert agents. The system is designed to help manage work as a CTO through intelligent task delegation and coordination.

## Technology Stack

- **Language**: Python 3.14+
- **Package Manager**: uv (modern Python package manager)
- **Project Type**: Application (not a library)
- **Agent Framework**: [Strands Agents](https://strandsagents.com/) (`strands-agents[otel]`) — provides the `Agent` class, `@tool` decorator, MCP client integration, hooks system, and OpenTelemetry support
- **Agent Tools**: `strands-agents-tools` — pre-built tools (e.g. `file_read`, `file_write`, `editor`, `handoff_to_user`)
- **LLM Backend**: Amazon Bedrock (via `strands.models.BedrockModel`)

## Build, Lint & Test Commands

### Environment Setup
```bash
# Ensure uv is installed (https://docs.astral.sh/uv/)
# The project uses Python 3.14 as specified in .python-version

# Install dependencies
uv sync

# Activate virtual environment (optional, uv commands work without activation)
source .venv/bin/activate
```

### Running the Application
```bash
# Run the main application
uv run main.py

# Run with OpenTelemetry export enabled
OTEL_EXPORTER_OTLP_ENDPOINT=http://localhost:4318 uv run main.py

# Run with debug logging
LOG_LEVEL=DEBUG uv run main.py
```

### Testing
The project uses `pytest` for testing.

```bash
# Run all tests
uv run pytest

# Run a single test file
uv run pytest tests/agents/github/test_auth.py

# Run with verbose output and showing print statements
uv run pytest -sv
```

### Linting & Formatting
`ruff` and `mypy` are already configured as dev dependencies in `pyproject.toml`.

```bash
# Format code
uv run ruff format .

# Check formatting without modifying files
uv run ruff format --check .

# Lint code
uv run ruff check .

# Lint with auto-fix
uv run ruff check --fix .

# Type checking
uv run mypy .
```

## Environment Variables

| Variable | Required | Description |
|---|---|---|
| `LOG_LEVEL` | No | Python logging level (e.g. `DEBUG`, `INFO`). Logging is disabled when unset. |
| `OTEL_EXPORTER_OTLP_ENDPOINT` | No | OTLP endpoint URL (e.g. `http://localhost:4318`) to enable OpenTelemetry tracing. |
| `AWS_*` / `AWS_PROFILE` | Yes | Standard AWS credentials for Amazon Bedrock access. |

### Running a local OTel collector
```bash
docker run \
  -p 127.0.0.1:4317:4317 \
  -p 127.0.0.1:4318:4318 \
  -p 127.0.0.1:55679:55679 \
  otel/opentelemetry-collector:0.144.0
```

## Project Structure

```
mAI-consigliere/
├── main.py                    # Application entry point; initializes telemetry and calls run_app()
├── pyproject.toml             # Project metadata and dependencies
├── uv.lock                    # Locked dependencies
├── .python-version            # Python version specification
├── README.md                  # Project documentation
├── agents/
│   ├── __init__.py
│   ├── hooks.py               # MutationApprovalHook — human-in-the-loop safety hook
│   ├── consigliere/           # Orchestrator agent package
│   │   ├── __init__.py
│   │   ├── config.py          # Model selection + system prompt for the orchestrator
│   │   └── main.py            # Orchestrator Agent setup + interactive loop
│   ├── github/                # GitHub specialist agent package (MCP-backed)
│   │   ├── __init__.py
│   │   ├── auth.py            # GitHub Device Flow authentication
│   │   ├── config.py
│   │   └── main.py            # @tool-decorated agent function + lazy MCP client
│   ├── jira/                  # Jira / Atlassian Rovo specialist agent package (MCP-backed)
│   │   ├── __init__.py
│   │   ├── auth.py            # Jira OAuth 2.0 provider configuration
│   │   ├── config.py
│   │   └── main.py            # @tool-decorated agent function + lazy MCP client
│   └── korean/                # Korean language specialist agent package
│       ├── __init__.py
│       ├── config.py
│       └── main.py            # @tool-decorated agent function
├── auth/                      # Shared OAuth utilities (used by Jira)
│   ├── __init__.py
│   ├── callback.py            # One-shot local HTTP server for OAuth 2.0 callback
│   └── storage.py             # File-based OAuth token/client-info storage
└── tests/                     # Unit tests
    ├── agents/
    │   ├── test_hooks.py      # Tests for shared MutationApprovalHook
    │   ├── github/
    │   │   └── test_auth.py   # Tests for GitHub auth flow
    │   ├── jira/
    │   │   └── test_auth.py   # Tests for Jira auth provider
    │   └── korean/
    │       └── test_main.py   # Tests for Korean assistant logic
    └── __init__.py
```

## Agent Architecture

### Orchestrator (`agents/consigliere/`)
The orchestrator is a Strands `Agent` instance managed by the `run_app()` function in `agents/consigliere/main.py`. It holds the strategic system prompt and routes user requests to specialist agents by calling them as tools.

### Specialist Agents (`agents/github/`, `agents/jira/`, `agents/korean/`)
Each specialist is implemented as a **`@tool`-decorated function** in its respective `main.py`. These functions internally create a fresh `Agent` for every invocation. This keeps agents stateless and avoids shared mutable state.

Authentication and MCP clients are initialized **lazily** inside these functions (using `@lru_cache`) to avoid side effects during application startup.

```python
from strands import Agent, tool

@tool
def my_assistant(query: str) -> str:
    """Short docstring — used by the LLM to decide when to call this tool."""
    agent = Agent(
        system_prompt=MY_SYSTEM_PROMPT,
        model=MY_MODEL,
        tools=[...],
    )
    return str(agent(query))
```

### MCP Integration
Both GitHub and Jira agents connect to external **MCP servers** over streamable HTTP using `strands.tools.mcp.MCPClient`. Clients are lazily initialized only when the specialist tool is first called.

```python
from mcp.client.streamable_http import streamable_http_client
from strands.tools.mcp import MCPClient

def _get_mcp_client() -> MCPClient:
    # Lazy initialization logic here
    ...

@tool
def mcp_assistant(query: str) -> str:
    mcp_client = _get_mcp_client()
    with mcp_client:
        mcp_tools = mcp_client.list_tools_sync()
        agent = Agent(..., tools=mcp_tools)
        return str(agent(query))
```

### Human-in-the-loop / Mutation Approval
`agents/hooks.py` provides `MutationApprovalHook`, a Strands `HookProvider` that intercepts every **mutating** tool call (e.g. creating/updating GitHub issues) before execution and prompts the user for explicit approval via stdin. It is the code-enforcement layer — it fires even if the agent's system prompt fails to ask for consent.

```python
from agents.hooks import MutationApprovalHook

agent = Agent(
    ...,
    hooks=[MutationApprovalHook(MUTATING_TOOLS)],  # frozenset of tool names
)
```

## Authentication

### GitHub (Device Flow OAuth)
`agents/github/auth.py` implements GitHub's [device authorization flow](https://docs.github.com/en/apps/oauth-apps/building-oauth-apps/authorizing-oauth-apps#device-flow):
1. On first run (when the tool is called), a user code is printed and the user visits `https://github.com/login/device`.
2. After approval, an access token is fetched and **persisted to disk** (path configured in `agents/github/config.py`).
3. Subsequent runs read the token from disk — no browser needed.

### Jira / Atlassian Rovo (OAuth 2.0 + local callback)
`agents/jira/auth.py` configures `mcp.client.auth.OAuthClientProvider`:
1. A local one-shot HTTP server (`auth/callback.py`) listens on a configurable port (default `9876`) for the OAuth redirect.
2. The system browser is opened automatically for the Atlassian login page.
3. After authentication, tokens are persisted via `auth/storage.py` (`FileTokenStorage`).
4. Refresh tokens are handled automatically on subsequent runs.

## Code Style Guidelines

### Imports
- Use standard library imports first, then third-party, then local imports
- Group imports in alphabetical order within each group
- Use absolute imports for project modules
- Avoid wildcard imports (`from module import *`)

Example:
```python
import os
import sys
from typing import Any

from strands import Agent, tool
from strands.models import BedrockModel

from agents.hooks import MutationApprovalHook
```

### Formatting
- **Line Length**: 88 characters (Ruff default)
- **Indentation**: 4 spaces (no tabs)
- **Quotes**: Double quotes for strings
- **Trailing Commas**: Use in multi-line structures

### Type Hints
- Use type hints for all function signatures
- Use `typing` module types for complex types
- Document return types, even if `None`
- Use modern Python 3.14+ union syntax (`X | Y`) where applicable

Example:
```python
def process_task(task_id: str, metadata: dict[str, Any] | None = None) -> dict[str, str]:
    """Process a task with given ID and optional metadata."""
    pass
```

### Naming Conventions
- **Modules**: `lowercase_with_underscores.py`
- **Classes**: `PascalCase`
- **Functions/Methods**: `snake_case`
- **Constants**: `UPPER_CASE_WITH_UNDERSCORES`
- **Private members**: `_leading_underscore`
- **Agent tools**: name the `@tool` function after the specialist (e.g. `github_assistant`, `jira_assistant`)

### Error Handling
- Use specific exception types, not bare `except:`
- Always provide meaningful error messages
- Use context managers (`with` statements) for resource management
- Log errors with appropriate context before re-raising

Example:
```python
try:
    result = perform_operation()
except ValueError as e:
    logger.error(f"Invalid value in operation: {e}")
    raise
except Exception as e:
    logger.exception("Unexpected error in operation")
    raise RuntimeError(f"Operation failed: {e}") from e
```

### Documentation
- Use docstrings for all public modules, classes, and functions
- Follow Google or NumPy docstring style
- Document parameters, return values, and exceptions
- Keep comments concise and explain "why", not "what"
- The docstring of a `@tool` function is shown to the LLM — keep it clear and accurate so the orchestrator can route correctly

Example:
```python
@tool
def my_assistant(query: str) -> str:
    """
    Handle questions about <domain>.

    Args:
        query: The user's question about <domain>

    Returns:
        A helpful answer based on <domain> data
    """
    ...
```

## Development Workflow

1. **Before Making Changes**
   - Read relevant code to understand context
   - Check for existing patterns and conventions
   - Consider agent architecture and communication patterns

2. **When Adding a New Specialist Agent**
   - Create a new directory under `agents/` with `__init__.py`, `config.py`, and `main.py`
   - Implement the agent as a `@tool`-decorated function (see Agent Architecture above)
   - Add the tool to the orchestrator's `tools=[...]` list in `main.py`
   - If the agent needs MCP, follow the pattern in `agents/github/` or `agents/jira/`
   - If the agent performs mutations, add `MutationApprovalHook` (see `agents/github/main.py`)

3. **When Modifying Code**
   - Preserve existing naming conventions
   - Update docstrings if behaviour changes
   - Ensure changes maintain agent isolation (agents should be stateless)

4. **After Making Changes**
   - Run linter: `uv run ruff check .`
   - Run formatter: `uv run ruff format .`
   - Run type checker: `uv run mypy .`
   - Run tests (once implemented): `uv run pytest`
   - Update documentation if adding features

## Additional Notes

- This project uses `uv` which is significantly faster than pip
- Agents are intentionally **stateless** — a fresh `Agent` instance is created per invocation inside each `@tool` function
- The `@tool` docstring is the contract between the orchestrator LLM and the specialist — keep it precise
- For MCP-backed agents, tools are discovered dynamically at runtime; no hardcoded tool lists are needed
- OpenTelemetry tracing is supported out of the box via `strands-agents[otel]` — set `OTEL_EXPORTER_OTLP_ENDPOINT` to enable it
