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

### Testing
Currently no test framework is configured. When adding tests:

```bash
# Install pytest (recommended)
uv add --dev pytest pytest-cov pytest-asyncio

# Run all tests
uv run pytest

# Run a single test file
uv run pytest tests/test_file.py

# Run a single test function
uv run pytest tests/test_file.py::test_function_name

# Run tests with coverage
uv run pytest --cov=. --cov-report=html
```

### Linting & Formatting

```bash
# Add ruff (modern, fast linter and formatter)
uv add --dev ruff

# Format code
uv run ruff format .

# Check formatting
uv run ruff format --check .

# Lint code
uv run ruff check .

# Lint with auto-fix
uv run ruff check --fix .

# Type checking with mypy
uv add --dev mypy
uv run mypy .
```
