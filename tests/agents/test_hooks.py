"""Tests for agents/hooks.py — MutationApprovalHook."""

from unittest.mock import MagicMock
from strands.hooks import BeforeToolCallEvent
from agents.hooks import MutationApprovalHook

MUTATING_TOOLS = frozenset({"create_issue", "delete_repo"})


def test_hook_ignores_non_mutating_tools():
    hook = MutationApprovalHook(MUTATING_TOOLS)
    event = MagicMock(spec=BeforeToolCallEvent)
    event.tool_use = {"name": "get_issue", "input": {"id": 123}}
    event.cancel_tool = None  # Initialize to None
    
    hook.require_approval(event)
    
    event.interrupt.assert_not_called()
    assert event.cancel_tool is None


def test_hook_interrupts_mutating_tool():
    hook = MutationApprovalHook(MUTATING_TOOLS)
    event = MagicMock(spec=BeforeToolCallEvent)
    event.tool_use = {"name": "create_issue", "input": {"title": "Bug"}}
    event.interrupt.return_value = "yes"
    event.cancel_tool = None
    
    hook.require_approval(event)
    
    event.interrupt.assert_called_once_with(
        "mutation-approval",
        reason={"tool": "create_issue", "input": {"title": "Bug"}}
    )
    assert event.cancel_tool is None


def test_hook_cancels_on_rejection():
    hook = MutationApprovalHook(MUTATING_TOOLS)
    event = MagicMock(spec=BeforeToolCallEvent)
    event.tool_use = {"name": "delete_repo", "input": {"name": "my-repo"}}
    event.interrupt.return_value = "no"
    event.cancel_tool = None
    
    hook.require_approval(event)
    
    assert event.cancel_tool == "Operation cancelled by user."


def test_hook_accepts_various_yes_inputs():
    hook = MutationApprovalHook(MUTATING_TOOLS)
    for yes_input in ["y", "Y", "yes", " YES ", "yEs"]:
        event = MagicMock(spec=BeforeToolCallEvent)
        event.tool_use = {"name": "create_issue", "input": {}}
        event.interrupt.return_value = yes_input
        event.cancel_tool = None
        
        hook.require_approval(event)
        
        assert event.cancel_tool is None


def test_hook_cancels_on_empty_or_random_input():
    hook = MutationApprovalHook(MUTATING_TOOLS)
    for bad_input in ["", "  ", "maybe", "cancel"]:
        event = MagicMock(spec=BeforeToolCallEvent)
        event.tool_use = {"name": "create_issue", "input": {}}
        event.interrupt.return_value = bad_input
        event.cancel_tool = None
        
        hook.require_approval(event)
        
        assert event.cancel_tool == "Operation cancelled by user."
