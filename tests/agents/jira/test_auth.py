"""Tests for agents/jira/auth.py."""

import functools
from pathlib import Path

from agents.jira.auth import get_jira_oauth_provider
from agents.jira.config import REDIRECT_URI, ROVO_MCP_URL, TOKEN_FILE
from auth.storage import FileTokenStorage


def test_get_jira_oauth_provider_defaults() -> None:
    provider = get_jira_oauth_provider()

    assert provider.context.server_url == ROVO_MCP_URL
    assert provider.context.client_metadata.client_name == "mAI Consigliere"

    redirect_uris = provider.context.client_metadata.redirect_uris
    assert redirect_uris is not None
    assert str(redirect_uris[0]) == REDIRECT_URI

    storage = provider.context.storage
    assert isinstance(storage, FileTokenStorage)
    assert storage._path == TOKEN_FILE


def test_get_jira_oauth_provider_custom_values(tmp_path: Path) -> None:
    custom_token_file = tmp_path / "jira_token.json"
    custom_port = 1234
    expected_redirect = f"http://localhost:{custom_port}/callback"

    provider = get_jira_oauth_provider(
        token_file=custom_token_file, callback_port=custom_port
    )

    storage = provider.context.storage
    assert isinstance(storage, FileTokenStorage)
    assert storage._path == custom_token_file

    redirect_uris = provider.context.client_metadata.redirect_uris
    assert redirect_uris is not None
    assert str(redirect_uris[0]) == expected_redirect

    callback_handler = provider.context.callback_handler
    assert isinstance(callback_handler, functools.partial)
    assert callback_handler.keywords["port"] == custom_port
