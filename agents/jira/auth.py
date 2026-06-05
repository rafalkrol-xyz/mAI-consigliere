"""Authentication logic for the Jira Assistant."""

import functools
from pathlib import Path
from typing import Optional

from mcp.client.auth import OAuthClientProvider
from mcp.shared.auth import OAuthClientMetadata
from pydantic import AnyUrl

from auth.storage import FileTokenStorage
from auth.callback import local_callback, open_browser
from agents.jira.config import (
    ROVO_MCP_URL,
    TOKEN_FILE,
    CALLBACK_PORT,
    REDIRECT_URI,
)


def get_jira_oauth_provider(
    token_file: Optional[Path] = None,
    callback_port: Optional[int] = None,
) -> OAuthClientProvider:
    """Get the Jira OAuth client provider.

    Args:
        token_file: Optional Path to the token storage file.
        callback_port: Optional port for the local callback server.

    Returns:
        The OAuthClientProvider instance.
    """
    path = token_file or TOKEN_FILE
    port = callback_port or CALLBACK_PORT
    redirect_uri = f"http://localhost:{port}/callback" if callback_port else REDIRECT_URI

    return OAuthClientProvider(
        server_url=ROVO_MCP_URL,
        client_metadata=OAuthClientMetadata(
            redirect_uris=[AnyUrl(redirect_uri)],
            client_name="mAI Consigliere",
            grant_types=["authorization_code", "refresh_token"],
            token_endpoint_auth_method="none",
        ),
        storage=FileTokenStorage(path),
        redirect_handler=open_browser,
        callback_handler=functools.partial(local_callback, port=port),
    )
