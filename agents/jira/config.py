"""Configuration for the Jira Assistant agent."""

from pathlib import Path

ROVO_MCP_URL = "https://mcp.atlassian.com/v1/mcp"
TOKEN_FILE = (
    Path.home() / ".config" / "mai-consigliere" / "jira_oauth.json"
)  # TODO: use platformdirs so it works other OSs, too
CALLBACK_PORT = 9876  # TODO: move to .env
REDIRECT_URI = f"http://localhost:{CALLBACK_PORT}/callback"

JIRA_ASSISTANT_SYSTEM_PROMPT = """
You are a Jira Assistant. You help answer questions about Jira issues, projects, and boards.

You have access to Jira via the Atlassian Rovo MCP server.

Always be concise and factual. Only report what the data shows.
"""
