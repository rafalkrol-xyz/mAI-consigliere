import time
from pathlib import Path

import httpx
from strands import Agent, tool

from mcp.client.streamable_http import streamable_http_client
from strands.tools.mcp import MCPClient

_CLIENT_ID = "178c6fc778ccc68e1d6a"  # GitHub CLI's public client_id
# TODO: use the keyring library to avoid storing the token in plain text
# https://pypi.org/project/keyring/
_TOKEN_FILE = Path.home() / ".config" / "mai-consigliere" / "github_token"


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

    print(f"\nOpen https://github.com/login/device and enter code: {data['user_code']}\n")

    interval = data.get("interval", 5)
    while True:
        time.sleep(interval)
        poll = httpx.post(
            "https://github.com/login/oauth/access_token",
            data={"client_id": _CLIENT_ID, "device_code": data["device_code"], "grant_type": "urn:ietf:params:oauth:grant-type:device_code"},
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

GITHUB_ASSISTANT_SYSTEM_PROMPT = """
You are a GitHub Assistant. You help answer questions about my private GitHub issues, project and repositories.

You have read-only access to GitHub issues.

Always be concise and factual. Only report what the data shows.
"""


_github_token = _get_github_token()
github_mcp_client = MCPClient(
    lambda: streamable_http_client(
        url="https://api.githubcopilot.com/mcp/",
        http_client=httpx.AsyncClient(headers={"Authorization": f"Bearer {_github_token}"}),
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
        with github_mcp_client:
            tools = github_mcp_client.list_tools_sync()
            agent = Agent(
                system_prompt=GITHUB_ASSISTANT_SYSTEM_PROMPT,
                tools=tools,
            )
            agent_response = agent(query)
            text_response = str(agent_response)

            if len(text_response) > 0:
                return text_response

            return "I apologize, but I couldn't properly analyze your GitHub-related question. Could you please rephrase or provide more context?"
    except Exception as e:
        return f"Error processing GitHub query: {e}"
