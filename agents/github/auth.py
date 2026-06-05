"""Authentication logic for the GitHub Assistant."""

import time
from pathlib import Path
from typing import Optional

import httpx

from agents.github.config import CLIENT_ID, TOKEN_FILE


def get_github_token(
    client: Optional[httpx.Client] = None,
    token_file: Optional[Path] = None,
    client_id: str = CLIENT_ID,
) -> str:
    """Get the GitHub OAuth token, either from storage or via device flow.

    Args:
        client: Optional httpx.Client for network requests (useful for mocking).
        token_file: Optional Path to the token storage file.
        client_id: The GitHub OAuth client ID.

    Returns:
        The GitHub access token.
    """
    token_path = token_file or TOKEN_FILE
    if token_path.exists():
        return token_path.read_text().strip()

    _client = client or httpx.Client()

    # Equivalent curl command:
    # curl -X POST "https://github.com/login/device/code" \
    #      -H "Accept: application/json" \
    #      -d "client_id=178c6fc778ccc68e1d6a&scope=repo"

    r = _client.post(
        "https://github.com/login/device/code",
        data={"client_id": client_id, "scope": "repo"},
        headers={"Accept": "application/json"},
    )
    r.raise_for_status()
    data = r.json()

    print(
        f"\nOpen https://github.com/login/device and enter code: {data['user_code']}\n"
    )

    interval = data.get("interval", 5)
    while True:
        time.sleep(interval)
        poll = _client.post(
            "https://github.com/login/oauth/access_token",
            data={
                "client_id": client_id,
                "device_code": data["device_code"],
                "grant_type": "urn:ietf:params:oauth:grant-type:device_code",
            },
            headers={"Accept": "application/json"},
        )
        poll.raise_for_status()
        result = poll.json()
        if "access_token" in result:
            token = result["access_token"]
            token_path.parent.mkdir(parents=True, exist_ok=True)
            token_path.write_text(token)
            print("GitHub authentication successful.\n")
            return token
        if result.get("error") not in ("authorization_pending", "slow_down"):
            raise RuntimeError(f"Device flow failed: {result}")
        if result.get("error") == "slow_down":
            interval += 5
