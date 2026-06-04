from typing import Any

from strands.hooks import BeforeToolCallEvent, HookProvider, HookRegistry


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
