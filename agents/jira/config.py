"""Configuration for the Jira Assistant agent."""

from pathlib import Path

from strands.models import BedrockModel

JIRA_ASSISTANT_MODEL = BedrockModel(
    # eu.anthropic.claude-opus-4-6-v1
    # eu.anthropic.claude-sonnet-4-6
    # eu.anthropic.claude-haiku-4-5-20251001-v1:0
    # eu.amazon.nova-2-lite-v1:0
    # qwen.qwen3-235b-a22b-2507-v1:0
    # qwen.qwen3-coder-30b-a3b-v1:0
    model_id="eu.anthropic.claude-sonnet-4-6"
)

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
