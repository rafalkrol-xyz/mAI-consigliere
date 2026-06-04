"""GitHub Assistant agent."""

import json
import time

import httpx
from strands import Agent, tool
from strands.types.interrupt import InterruptResponseContent

from mcp.client.streamable_http import streamable_http_client
from strands.tools.mcp import MCPClient
from strands_tools import handoff_to_user

from agents.hooks import MutationApprovalHook
from agents.github.config import (
    CLIENT_ID,
    TOKEN_FILE,
    GITHUB_ASSISTANT_SYSTEM_PROMPT,
    GITHUB_MUTATING_TOOLS,
)


def _get_github_token() -> str:
    if TOKEN_FILE.exists():
        return TOKEN_FILE.read_text().strip()

    # Equivalent curl command:
    # curl -X POST "https://github.com/login/device/code" \
    #      -H "Accept: application/json" \
    #      -d "client_id=178c6fc778ccc68e1d6a&scope=repo"

    r = httpx.post(
        "https://github.com/login/device/code",
        data={"client_id": CLIENT_ID, "scope": "repo"},
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
            TOKEN_FILE.parent.mkdir(parents=True, exist_ok=True)
            TOKEN_FILE.write_text(token)
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
def github_assistant(query: str) -> str:
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
                # MutationApprovalHook: enforcement layer — intercepts every
                # mutating tool call before execution regardless of whether
                # the agent called handoff_to_user first.
                hooks=[MutationApprovalHook(GITHUB_MUTATING_TOOLS)],
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
