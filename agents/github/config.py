"""Configuration for the GitHub Projects Assistant agent."""

from pathlib import Path

from strands.models import BedrockModel

GITHUB_ASSISTANT_MODEL = BedrockModel(
    # eu.anthropic.claude-opus-4-6-v1
    # eu.anthropic.claude-sonnet-4-6
    # eu.anthropic.claude-haiku-4-5-20251001-v1:0
    # eu.amazon.nova-2-lite-v1:0
    # qwen.qwen3-235b-a22b-2507-v1:0
    # qwen.qwen3-coder-30b-a3b-v1:0
    model_id="eu.anthropic.claude-sonnet-4-6"
)

CLIENT_ID = "178c6fc778ccc68e1d6a"  # GitHub CLI's public client_id
# TODO: use the keyring library to avoid storing the token in plain text
# https://pypi.org/project/keyring/
TOKEN_FILE = Path.home() / ".config" / "mai-consigliere" / "github_token"

# ⚠️  SECURITY WARNING — SCOPE vs. SYSTEM PROMPT MISMATCH
#
# The OAuth token is issued with the broad `repo` scope AND the GitHub Copilot
# MCP server (https://api.githubcopilot.com/mcp/) exposes a far wider tool
# surface than what the system prompt describes. Any tool the MCP server
# provides CAN be invoked by the agent if the LLM decides to call it.
#
# Known MCP tool categories and operations (with `repo` scope):
#
#   Issues (intended use):
#     - list_issues, get_issue, search_issues
#     - create_issue, update_issue (incl. close/reopen/archive)
#     - add_issue_comment, list_issue_comments
#     - assign_copilot_to_issue
#
#   Pull Requests (UNINTENDED for now):
#     - list_pull_requests, get_pull_request
#     - create_pull_request, update_pull_request, merge_pull_request
#     - add_pull_request_review, create_pull_request_review
#     - get_pull_request_diff, get_pull_request_files, list_pull_request_files
#
#   Repository & Code (UNINTENDED for now):
#     - get_file_contents, create_or_update_file, delete_file
#     - search_code, list_branches, create_branch, get_commit
#     - push_files (multi-file commit)
#     - create_repository, fork_repository
#
#   Notifications (UNINTENDED for now):
#     - list_notifications, get_notification_thread, mark_notification_as_read
#     - mark_all_notifications_as_read, dismiss_notification
#
#   Users / Search (UNINTENDED for now):
#     - get_authenticated_user, search_users, search_repositories
GITHUB_ASSISTANT_SYSTEM_PROMPT = """
You are a GitHub Assistant. You help answer questions about my private GitHub issues, projects and repositories.

You have read and write access to GitHub issues and more (see tool list).
Before executing ANY write or mutating operation (creating, updating, closing, merging, deleting, commenting, archiving, pushing, forking, etc.),
you MUST first call the `handoff_to_user` tool to:
1. Clearly describe the exact action you are about to take and its parameters.
2. Ask the user for explicit confirmation ("yes" / "no").

Only proceed with the write operation if the user confirms. If the user declines, explain that the operation was cancelled and suggest alternatives.

Always be concise and factual. Only report what the data shows.
"""

# All known GitHub MCP tools that perform write / mutating operations.
# The BeforeToolCallEvent hook will intercept any call to these and require
# explicit human approval before the tool is allowed to execute.
GITHUB_MUTATING_TOOLS: frozenset[str] = frozenset(
    {
        # Issues
        "create_issue",
        "update_issue",
        "add_issue_comment",
        "assign_copilot_to_issue",
        #
        # Pull Requests
        "create_pull_request",
        "update_pull_request",
        "merge_pull_request",
        "add_pull_request_review",
        "create_pull_request_review",
        #
        # Repository & Code
        "create_or_update_file",
        "delete_file",
        "push_files",
        "create_branch",
        "create_repository",
        "fork_repository",
        #
        # Notifications
        "mark_notification_as_read",
        "mark_all_notifications_as_read",
        "dismiss_notification",
    }
)
