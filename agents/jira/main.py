"""Jira Assistant agent."""

from functools import lru_cache

import httpx
from strands import Agent, tool

from mcp.client.streamable_http import streamable_http_client
from strands.tools.mcp import MCPClient

from agents.jira.auth import get_jira_oauth_provider
from agents.jira.config import (
    ROVO_MCP_URL,
    JIRA_ASSISTANT_MODEL,
    JIRA_ASSISTANT_SYSTEM_PROMPT,
)


@lru_cache(maxsize=1)
def _get_mcp_client() -> MCPClient:
    """Lazily initialize and return the Jira MCP client."""
    oauth = get_jira_oauth_provider()
    return MCPClient(
        lambda: streamable_http_client(
            url=ROVO_MCP_URL,
            http_client=httpx.AsyncClient(auth=oauth),
        )
    )


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
        mcp_client = _get_mcp_client()
        with mcp_client:
            tools = mcp_client.list_tools_sync()
            agent = Agent(
                system_prompt=JIRA_ASSISTANT_SYSTEM_PROMPT,
                model=JIRA_ASSISTANT_MODEL,
                tools=tools,
            )
            agent_response = agent(query)
            text_response = str(agent_response)

            if len(text_response) > 0:
                return text_response

            return "I apologize, but I couldn't properly analyze your Jira-related question. Could you please rephrase or provide more context?"
    except Exception as e:
        return f"Error processing Jira query: {e}"
