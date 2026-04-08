import functools
from pathlib import Path

import httpx
from strands import Agent, tool

from mcp.client.auth import OAuthClientProvider
from mcp.client.streamable_http import streamable_http_client
from mcp.shared.auth import OAuthClientMetadata
from pydantic import AnyUrl
from strands.tools.mcp import MCPClient

from auth.storage import FileTokenStorage
from auth.callback import local_callback, open_browser

_ROVO_MCP_URL = "https://mcp.atlassian.com/v1/mcp"
_TOKEN_FILE = (
    Path.home() / ".config" / "mai-consigliere" / "jira_oauth.json"
)  # TODO: use platformdirs so it works other OSs, too
_CALLBACK_PORT = 9876 # TODO: move to .env
_REDIRECT_URI = f"http://localhost:{_CALLBACK_PORT}/callback"


_oauth = OAuthClientProvider(
    server_url=_ROVO_MCP_URL,
    client_metadata=OAuthClientMetadata(
        redirect_uris=[AnyUrl(_REDIRECT_URI)],
        client_name="mAI Consigliere",
        grant_types=["authorization_code", "refresh_token"],
        token_endpoint_auth_method="none",
    ),
    storage=FileTokenStorage(_TOKEN_FILE),
    redirect_handler=open_browser,
    callback_handler=functools.partial(local_callback, port=_CALLBACK_PORT),
)

_jira_mcp_client = MCPClient(
    lambda: streamable_http_client(
        url=_ROVO_MCP_URL,
        http_client=httpx.AsyncClient(auth=_oauth),
    )
)

JIRA_ASSISTANT_SYSTEM_PROMPT = """
You are a Jira Assistant. You help answer questions about Jira issues, projects, and boards.

You have access to Jira via the Atlassian Rovo MCP server.

Always be concise and factual. Only report what the data shows.
"""


@tool
def jira_assistant(query: str) -> str:
    """
    Answer questions about Jira issues, projects, and boards.

    Args:
        query: The user's question about Jira

    Returns:
        A helpful answer based on Jira data
    """
    try:
        print("Routed to Jira Assistant")
        with _jira_mcp_client:
            tools = _jira_mcp_client.list_tools_sync()
            agent = Agent(
                system_prompt=JIRA_ASSISTANT_SYSTEM_PROMPT,
                tools=tools,
            )
            agent_response = agent(query)
            text_response = str(agent_response)

            if len(text_response) > 0:
                return text_response

            return "I apologize, but I couldn't properly analyze your Jira-related question. Could you please rephrase or provide more context?"
    except Exception as e:
        return f"Error processing Jira query: {e}"
