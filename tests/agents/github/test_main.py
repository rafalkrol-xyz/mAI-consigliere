"""Tests for agents/github/main.py."""

from unittest.mock import patch

from agents.github.main import _get_mcp_client


class TestGetMcpClient:
    """Tests for the _get_mcp_client() factory function."""

    def test_returns_new_instance_on_every_call(self) -> None:
        """_get_mcp_client() must NOT cache its result.

        The MCPClient context manager closes (and tears down) the connection on
        __exit__.  If the same instance were returned on a second call the MCP
        session would already be closed, causing RuntimeError / MCPClientInitializationError
        on every subsequent tool invocation.  Each call must therefore return a
        distinct object.
        """
        with patch("agents.github.main.get_github_token", return_value="ghp_test"):
            client_1 = _get_mcp_client()
            client_2 = _get_mcp_client()

        assert client_1 is not client_2
