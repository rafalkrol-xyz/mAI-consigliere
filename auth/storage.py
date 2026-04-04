from pathlib import Path
import json

from mcp.shared.auth import OAuthClientInformationFull, OAuthToken

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
