# AI Agent Guidelines for mAI-consigliere

This document provides essential information for AI coding agents working in this repository.

## Project Overview

**mAI-consigliere** is an agentic AI system comprising an orchestrator agent (the "mAI Consigliere") and multiple specialized expert agents. The system is designed to help manage work as a CTO through intelligent task delegation and coordination.

## Technology Stack

- **Language**: Python 3.14+
- **Package Manager**: uv (modern Python package manager)
- **Project Type**: Application (not a library)

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
Currently no linting/formatting tools are configured. Recommended setup:

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
from typing import Any, Dict, List

import anthropic
import openai

from agents.base import BaseAgent
from utils.logger import setup_logger
```

### Formatting
- **Line Length**: 88 characters (Black/Ruff default)
- **Indentation**: 4 spaces (no tabs)
- **Quotes**: Double quotes for strings (configurable)
- **Trailing Commas**: Use in multi-line structures

### Type Hints
- Use type hints for all function signatures
- Use `typing` module types for complex types
- Document return types, even if `None`
- Use modern Python 3.10+ syntax where applicable

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
- **Agents**: End class names with `Agent` (e.g., `OrchestratorAgent`, `CodeReviewAgent`)

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

Example:
```python
def create_agent(agent_type: str, config: dict[str, Any]) -> BaseAgent:
    """Create and initialize an agent of the specified type.
    
    Args:
        agent_type: Type identifier for the agent (e.g., "orchestrator", "expert")
        config: Configuration dictionary for agent initialization
        
    Returns:
        Initialized agent instance
        
    Raises:
        ValueError: If agent_type is not recognized
        ConfigurationError: If config is invalid
    """
    pass
```

## Project Structure

```
mAI-consigliere/
├── main.py              # Application entry point
├── pyproject.toml       # Project metadata and dependencies
├── uv.lock              # Locked dependencies
├── .python-version      # Python version specification
├── README.md            # Project documentation
└── .venv/               # Virtual environment (gitignored)
```

As the project grows, consider this structure:
```
mAI-consigliere/
├── agents/              # Agent implementations
│   ├── __init__.py
│   ├── base.py         # Base agent class
│   ├── orchestrator.py # Main orchestrator agent
│   └── experts/        # Specialized expert agents
├── utils/              # Utility modules
├── config/             # Configuration files
├── tests/              # Test files
└── main.py
```

## Development Workflow

1. **Before Making Changes**
   - Read relevant code to understand context
   - Check for existing patterns and conventions
   - Consider agent architecture and communication patterns

2. **When Adding New Code**
   - Create new agent classes by inheriting from `BaseAgent` (when implemented)
   - Maintain clear separation between orchestrator and expert agents
   - Write type hints and docstrings
   - Consider async/await patterns for agent communication

3. **When Modifying Code**
   - Preserve existing naming conventions
   - Update docstrings if behavior changes
   - Ensure changes maintain agent isolation

4. **After Making Changes**
   - Run linter and formatter (once configured)
   - Run tests (once implemented)
   - Update documentation if adding features

## Additional Notes

- This project uses `uv` which is significantly faster than pip
- No configuration files for linting/testing exist yet - establish conventions early
- Focus on clean agent abstractions and clear communication protocols
- Consider async patterns for agent coordination
- Keep agents stateless where possible for better testability
