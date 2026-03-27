from strands import Agent, tool

from mcp.client.sse import sse_client
from strands.tools.mcp import MCPClient

GITHUB_ASSISTANT_SYSTEM_PROMPT = """
You are a GitHub Projects Assistant. You help answer questions about GitHub issues and project status.

You have read-only access to GitHub issues. You can:
- List open issues in a repository
- Get details about specific issues (title, body, labels, assignees, comments)
- Summarize issue status, priorities, and themes
- Answer questions about project progress based on issue data

Always be concise and factual. Only report what the data shows.
"""


sse_mcp_client = MCPClient(lambda: sse_client("https://api.githubcopilot.com/mcp/"))

with sse_mcp_client:
    tools = sse_mcp_client.list_tools_sync()

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
