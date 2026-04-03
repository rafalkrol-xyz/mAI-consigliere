import json
import webbrowser
from pathlib import Path

import httpx
from strands import Agent, tool

from mcp.client.auth import OAuthClientProvider, TokenStorage
from mcp.client.streamable_http import streamable_http_client
from mcp.shared.auth import OAuthClientInformationFull, OAuthClientMetadata, OAuthToken
from strands.tools.mcp import MCPClient

_ROVO_MCP_URL = "https://mcp.atlassian.com/v1/mcp"
_TOKEN_FILE = Path.home() / ".config" / "mai-consigliere" / "jira_oauth.json"
_REDIRECT_URI = "http://localhost:9876/callback"


class _FileTokenStorage:
    """Persist OAuth tokens and client registration to disk."""

    def __init__(self, path: Path) -> None:
        self._path = path
        self._data: dict = json.loads(path.read_text()) if path.exists() else {}

    def _save(self) -> None:
        self._path.parent.mkdir(parents=True, exist_ok=True)
        self._path.write_text(json.dumps(self._data))

    async def get_tokens(self) -> OAuthToken | None:
        raw = self._data.get("tokens")
        return OAuthToken.model_validate(raw) if raw else None

    async def set_tokens(self, tokens: OAuthToken) -> None:
        self._data["tokens"] = tokens.model_dump(mode="json")
        self._save()

    async def get_client_info(self) -> OAuthClientInformationFull | None:
        raw = self._data.get("client_info")
        return OAuthClientInformationFull.model_validate(raw) if raw else None

    async def set_client_info(self, client_info: OAuthClientInformationFull) -> None:
        self._data["client_info"] = client_info.model_dump(mode="json")
        self._save()

TokenStorage.register(_FileTokenStorage)


async def _open_browser(url: str) -> None:
    print(f"\nOpening browser for Atlassian login...\nIf it doesn't open, visit:\n  {url}\n")
    webbrowser.open(url)


async def _local_callback() -> tuple[str, str | None]:
    """Spin up a one-shot HTTP server to capture the OAuth callback."""
    import asyncio
    from urllib.parse import parse_qs, urlparse

    result: dict = {}
    done = asyncio.Event()

    async def handle(reader: asyncio.StreamReader, writer: asyncio.StreamWriter) -> None:
        data = await reader.read(4096)
        request_line = data.decode().splitlines()[0]
        path = request_line.split(" ")[1]
        params = parse_qs(urlparse(path).query)
        result["code"] = params.get("code", [None])[0]
        result["state"] = params.get("state", [None])[0]
        writer.write(b"HTTP/1.1 200 OK\r\nContent-Type: text/html\r\n\r\n<h1>Authenticated! You can close this tab.</h1>")
        await writer.drain()
        writer.close()
        done.set()

    server = await asyncio.start_server(handle, "localhost", 9876)
    async with server:
        await done.wait()

    return result["code"], result.get("state")


_oauth = OAuthClientProvider(
    server_url=_ROVO_MCP_URL,
    client_metadata=OAuthClientMetadata(
        redirect_uris=[_REDIRECT_URI],  # type: ignore[arg-type]
        client_name="mAI Consigliere",
        grant_types=["authorization_code", "refresh_token"],
        token_endpoint_auth_method="none",
    ),
    storage=_FileTokenStorage(_TOKEN_FILE),
    redirect_handler=_open_browser,
    callback_handler=_local_callback,
)

jira_mcp_client = MCPClient(
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
        with jira_mcp_client:
            tools = jira_mcp_client.list_tools_sync()
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
