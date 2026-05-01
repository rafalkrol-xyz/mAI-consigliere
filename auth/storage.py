from pathlib import Path

from mcp.client.auth import TokenStorage
from mcp.shared.auth import OAuthClientInformationFull, OAuthToken
from pydantic import BaseModel


class _StoredData(BaseModel):
    tokens: OAuthToken | None = None
    client_info: OAuthClientInformationFull | None = None


class FileTokenStorage(TokenStorage):
    """Persist OAuth tokens and client registration to disk."""

    def __init__(self, path: Path) -> None:
        self._path = path
        self._data = (
            _StoredData.model_validate_json(path.read_text())
            if path.exists()
            else _StoredData()
        )

    def _save(self) -> None:
        self._path.parent.mkdir(parents=True, exist_ok=True)
        self._path.write_text(self._data.model_dump_json())

    async def get_tokens(self) -> OAuthToken | None:
        return self._data.tokens

    async def set_tokens(self, tokens: OAuthToken) -> None:
        self._data.tokens = tokens
        self._save()

    async def get_client_info(self) -> OAuthClientInformationFull | None:
        return self._data.client_info

    async def set_client_info(self, client_info: OAuthClientInformationFull) -> None:
        self._data.client_info = client_info
        self._save()
