import json
import time
from pathlib import Path

import httpx
from strands import Agent, tool
from strands.types.interrupt import InterruptResponseContent

from agents.hooks import MutationApprovalHook

from mcp.client.streamable_http import streamable_http_client
from strands.tools.mcp import MCPClient
from strands_tools import handoff_to_user

_CLIENT_ID = "178c6fc778ccc68e1d6a"  # GitHub CLI's public client_id
# TODO: use the keyring library to avoid storing the token in plain text
# https://pypi.org/project/keyring/
_TOKEN_FILE = Path.home() / ".config" / "mai-consigliere" / "github_token"

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
_GITHUB_MUTATING_TOOLS: frozenset[str] = frozenset(
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


def _get_github_token() -> str:
    if _TOKEN_FILE.exists():
        return _TOKEN_FILE.read_text().strip()

    # Equivalent curl command:
    # curl -X POST "https://github.com/login/device/code" \
    #      -H "Accept: application/json" \
    #      -d "client_id=178c6fc778ccc68e1d6a&scope=repo"

    r = httpx.post(
        "https://github.com/login/device/code",
        data={"client_id": _CLIENT_ID, "scope": "repo"},
        headers={"Accept": "application/json"},
    )
    r.raise_for_status()
    data = r.json()

    print(
        f"\nOpen https://github.com/login/device and enter code: {data['user_code']}\n"
    )

    interval = data.get("interval", 5)
    while True:
        time.sleep(interval)
        poll = httpx.post(
            "https://github.com/login/oauth/access_token",
            data={
                "client_id": _CLIENT_ID,
                "device_code": data["device_code"],
                "grant_type": "urn:ietf:params:oauth:grant-type:device_code",
            },
            headers={"Accept": "application/json"},
        )
        poll.raise_for_status()
        result = poll.json()
        if "access_token" in result:
            token = result["access_token"]
            _TOKEN_FILE.parent.mkdir(parents=True, exist_ok=True)
            _TOKEN_FILE.write_text(token)
            print("GitHub authentication successful.\n")
            return token
        if result.get("error") not in ("authorization_pending", "slow_down"):
            raise RuntimeError(f"Device flow failed: {result}")
        if result.get("error") == "slow_down":
            interval += 5


_github_token = _get_github_token()
_github_mcp_client = MCPClient(
    lambda: streamable_http_client(
        url="https://api.githubcopilot.com/mcp/",
        http_client=httpx.AsyncClient(
            headers={"Authorization": f"Bearer {_github_token}"}
        ),
    )
)


@tool
def github_projects_assistant(query: str) -> str:
    """
    Answer questions about GitHub project issues for a given repository.

    Args:
        query: The user's question about the project or its issues

    Returns:
        A helpful answer based on the repository's open issues
    """
    try:
        print("Routed to GitHub Projects Assistant")
        with _github_mcp_client:
            mcp_tools = _github_mcp_client.list_tools_sync()
            agent = Agent(
                system_prompt=GITHUB_ASSISTANT_SYSTEM_PROMPT,
                # handoff_to_user: UX layer — agent proactively asks for consent
                # mcp_tools: all GitHub MCP tools fetched at runtime
                tools=[handoff_to_user, *mcp_tools],
                # GitHubMutationApprovalHook: enforcement layer — intercepts
                # every mutating tool call before execution regardless of
                # whether the agent called handoff_to_user first.
                hooks=[MutationApprovalHook(_GITHUB_MUTATING_TOOLS)],
                callback_handler=None,
            )

            result = agent(query)

            # Handle interrupt loop: the BeforeToolCallEvent hook pauses the
            # agent and waits for human approval via stdin before resuming.
            while True:
                if result.stop_reason != "interrupt":
                    break

                responses: list[InterruptResponseContent] = []
                for interrupt in result.interrupts or []:
                    if interrupt.name == "mutation-approval":
                        tool_name = interrupt.reason.get("tool", "unknown")
                        tool_input = json.dumps(
                            interrupt.reason.get("input", {}), indent=2
                        )
                        user_input = input(
                            f"\n⚠️  GitHub write operation requested:\n"
                            f"  Tool : {tool_name}\n"
                            f"  Input: {tool_input}\n"
                            f"Approve? (y/N): "
                        )
                        responses.append(
                            {
                                "interruptResponse": {
                                    "interruptId": interrupt.id,
                                    "response": user_input,
                                }
                            }
                        )

                result = agent(responses)

            text_response = str(result)
            if len(text_response) > 0:
                return text_response

            return "I apologize, but I couldn't properly analyze your GitHub-related question. Could you please rephrase or provide more context?"
    except Exception as e:
        return f"Error processing GitHub query: {e}"
