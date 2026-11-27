# mAI-consigliere

## Overview

This is an Agentic AI system comprising of an orchestrator agent,
the title _mAI Consigliere_ (a pun on _mAI_ read as _my_ and [Godfather](https://en.wikipedia.org/wiki/The_Godfather_(novel))'s
[consigliere](https://en.wikipedia.org/wiki/Consigliere)), and multiple specialized expert agents, added as needed.

## Build, Lint & Test Commands

### Environment Setup
```bash
# Ensure uv is installed (https://docs.astral.sh/uv/)
# The project uses Python 3.14 as specified in .python-version

# Install dependencies
uv sync

# Activate virtual environment (OPTIONAL SINCE uv commands work without activation)
source .venv/bin/activate
```

### Running the Application
```bash
# Run the main application
uv run main.py

# Or with activated venv
python main.py
```

The CLI greets you with a boxed welcome banner (active model, working directory), shows a
"Thinking…" spinner while the agent works, and streams the response to your terminal as
Markdown (tables, bullets, and syntax-highlighted code fences included) as it's generated.

### Testing
```bash
# Run all tests
uv run pytest

# Run with verbose output and showing print statements
uv run pytest -sv

# Run a single test file
uv run pytest tests/agents/consigliere/test_cli.py

# Run a single test function
uv run pytest tests/agents/consigliere/test_cli.py::TestRenderBanner::test_renders_configured_model_id
```

### Linting & Formatting

```bash
# Format code
uv run ruff format .

# Check formatting
uv run ruff format --check .

# Lint code
uv run ruff check .

# Lint with auto-fix
uv run ruff check --fix .

# Type checking
uv run mypy .
```
