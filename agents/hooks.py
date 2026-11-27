from contextlib import ExitStack
from typing import Any

from strands.hooks import (
    AfterToolCallEvent,
    BeforeToolCallEvent,
    HookProvider,
    HookRegistry,
)

from agents.user_input import input_guard


class MutationApprovalHook(HookProvider):
    """Intercepts mutating tool calls and requires human approval before execution.

    This is the code-enforcement layer. Even if the LLM bypasses any system
    prompt instruction to ask the user first, this hook will still pause
    execution and prompt for approval before any write operation is executed.

    Args:
        mutating_tools: Set of tool names that require human approval.
    """

    def __init__(self, mutating_tools: frozenset[str]) -> None:
        self._mutating_tools = mutating_tools

    def register_hooks(self, registry: HookRegistry, **kwargs: Any) -> None:
        registry.add_callback(BeforeToolCallEvent, self.require_approval)

    def require_approval(self, event: BeforeToolCallEvent) -> None:
        if event.tool_use["name"] not in self._mutating_tools:
            return

        approval = event.interrupt(
            "mutation-approval",
            reason={"tool": event.tool_use["name"], "input": event.tool_use["input"]},
        )
        if str(approval).strip().lower() not in ("y", "yes"):
            event.cancel_tool = "Operation cancelled by user."


class PauseDisplayForInputHook(HookProvider):
    """Pauses the front-end's live display while interactive tools prompt.

    Tools like handoff_to_user read from the terminal themselves, so they
    can't go through ask_user(). This hook enters the registered input
    guard before such a tool runs and exits it once the tool finishes.

    Args:
        interactive_tools: Set of tool names that read user input directly.
    """

    def __init__(self, interactive_tools: frozenset[str]) -> None:
        self._interactive_tools = interactive_tools
        self._open: dict[str, ExitStack] = {}

    def register_hooks(self, registry: HookRegistry, **kwargs: Any) -> None:
        registry.add_callback(BeforeToolCallEvent, self._pause)
        registry.add_callback(AfterToolCallEvent, self._resume)

    def _pause(self, event: BeforeToolCallEvent) -> None:
        if event.tool_use["name"] not in self._interactive_tools:
            return
        stack = ExitStack()
        stack.enter_context(input_guard())
        self._open[event.tool_use["toolUseId"]] = stack

    def _resume(self, event: AfterToolCallEvent) -> None:
        stack = self._open.pop(event.tool_use["toolUseId"], None)
        if stack is not None:
            stack.close()
