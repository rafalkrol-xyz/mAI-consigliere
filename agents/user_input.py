"""Terminal input helper shared by specialist agents.

Specialists call ask_user() instead of input() so the front-end (the Rich
CLI) can suspend any live display while the user types.
"""

from collections.abc import Callable
from contextlib import AbstractContextManager, nullcontext

InputGuard = Callable[[], AbstractContextManager[object]]

_input_guard: InputGuard = nullcontext

def set_input_guard(guard: InputGuard) -> None:
    """Register a context-manager factory entered around every prompt."""
    global _input_guard
    _input_guard = guard

def ask_user(prompt: str) -> str:
    """Prompt the user on stdin, pausing any registered live display."""
    with _input_guard():
        return input(prompt)
