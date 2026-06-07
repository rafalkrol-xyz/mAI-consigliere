"""Tests for agents/github/auth.py — get_github_token()."""

from pathlib import Path
from unittest.mock import MagicMock, call, patch

import httpx
import pytest

from agents.github.auth import get_github_token


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_response(json_data: dict, status_code: int = 200) -> MagicMock:
    """Build a minimal mock httpx.Response."""
    resp = MagicMock(spec=httpx.Response)
    resp.status_code = status_code
    resp.json.return_value = json_data
    resp.raise_for_status = MagicMock()  # no-op by default
    return resp


def _make_client(*responses) -> MagicMock:
    """Build a mock httpx.Client whose .post() returns *responses* in order."""
    client = MagicMock(spec=httpx.Client)
    client.post.side_effect = list(responses)
    return client


# ---------------------------------------------------------------------------
# Group 1 — cached token on disk
# ---------------------------------------------------------------------------


def test_returns_cached_token_when_file_exists(tmp_path: Path) -> None:
    token_file = tmp_path / "github_token"
    token_file.write_text("ghp_cached_token\n")

    result = get_github_token(token_file=token_file)

    assert result == "ghp_cached_token"


def test_cached_token_is_stripped(tmp_path: Path) -> None:
    token_file = tmp_path / "github_token"
    token_file.write_text("  ghp_padded  \n")

    result = get_github_token(token_file=token_file)

    assert result == "ghp_padded"


def test_no_http_calls_when_token_file_exists(tmp_path: Path) -> None:
    token_file = tmp_path / "github_token"
    token_file.write_text("ghp_cached_token")
    client = MagicMock(spec=httpx.Client)

    get_github_token(client=client, token_file=token_file)

    client.post.assert_not_called()


# ---------------------------------------------------------------------------
# Group 2 — device flow: happy path
# ---------------------------------------------------------------------------


@patch("time.sleep", return_value=None)
def test_device_flow_returns_token_on_first_poll(mock_sleep, tmp_path: Path) -> None:
    token_file = tmp_path / "github_token"
    device_code_resp = _make_response(
        {"device_code": "dc1", "user_code": "ABC-123", "interval": 0}
    )
    token_resp = _make_response({"access_token": "ghp_new_token"})
    client = _make_client(device_code_resp, token_resp)

    result = get_github_token(client=client, token_file=token_file)

    assert result == "ghp_new_token"


@patch("time.sleep", return_value=None)
def test_device_flow_persists_token_to_disk(mock_sleep, tmp_path: Path) -> None:
    token_file = tmp_path / "subdir" / "github_token"
    device_code_resp = _make_response(
        {"device_code": "dc1", "user_code": "ABC-123", "interval": 0}
    )
    token_resp = _make_response({"access_token": "ghp_saved_token"})
    client = _make_client(device_code_resp, token_resp)

    get_github_token(client=client, token_file=token_file)

    assert token_file.read_text() == "ghp_saved_token"


@patch("time.sleep", return_value=None)
def test_device_flow_creates_parent_directories(mock_sleep, tmp_path: Path) -> None:
    token_file = tmp_path / "deeply" / "nested" / "github_token"
    device_code_resp = _make_response(
        {"device_code": "dc1", "user_code": "ABC-123", "interval": 0}
    )
    token_resp = _make_response({"access_token": "ghp_tok"})
    client = _make_client(device_code_resp, token_resp)

    get_github_token(client=client, token_file=token_file)

    assert token_file.exists()


# ---------------------------------------------------------------------------
# Group 3 — device flow: polling retries
# ---------------------------------------------------------------------------


@patch("time.sleep", return_value=None)
def test_device_flow_retries_on_authorization_pending(
    mock_sleep, tmp_path: Path
) -> None:
    token_file = tmp_path / "github_token"
    device_code_resp = _make_response(
        {"device_code": "dc1", "user_code": "ABC-123", "interval": 0}
    )
    pending = _make_response({"error": "authorization_pending"})
    token_resp = _make_response({"access_token": "ghp_tok"})
    client = _make_client(device_code_resp, pending, pending, token_resp)

    result = get_github_token(client=client, token_file=token_file)

    assert result == "ghp_tok"
    # device_code POST + 3 polls
    assert client.post.call_count == 4


@patch("time.sleep", return_value=None)
def test_device_flow_increases_interval_on_slow_down(
    mock_sleep, tmp_path: Path
) -> None:
    token_file = tmp_path / "github_token"
    initial_interval = 3
    device_code_resp = _make_response(
        {"device_code": "dc1", "user_code": "ABC-123", "interval": initial_interval}
    )
    slow_down = _make_response({"error": "slow_down"})
    token_resp = _make_response({"access_token": "ghp_tok"})
    client = _make_client(device_code_resp, slow_down, token_resp)

    get_github_token(client=client, token_file=token_file)

    # First poll sleep uses initial interval; second uses initial + 5
    sleep_calls = mock_sleep.call_args_list
    assert sleep_calls[0] == call(initial_interval)
    assert sleep_calls[1] == call(initial_interval + 5)


# ---------------------------------------------------------------------------
# Group 4 — device flow: error conditions
# ---------------------------------------------------------------------------


@patch("time.sleep", return_value=None)
def test_device_flow_raises_on_unexpected_error(mock_sleep, tmp_path: Path) -> None:
    token_file = tmp_path / "github_token"
    device_code_resp = _make_response(
        {"device_code": "dc1", "user_code": "ABC-123", "interval": 0}
    )
    error_resp = _make_response({"error": "expired_token"})
    client = _make_client(device_code_resp, error_resp)

    with pytest.raises(RuntimeError, match="Device flow failed"):
        get_github_token(client=client, token_file=token_file)


def test_device_flow_raises_on_http_error(tmp_path: Path) -> None:
    # raise_for_status fires on the first POST (device code request),
    # before the polling loop — so time.sleep is never called.
    token_file = tmp_path / "github_token"
    bad_resp = MagicMock(spec=httpx.Response)
    bad_resp.raise_for_status.side_effect = httpx.HTTPStatusError(
        "500 Server Error",
        request=MagicMock(),
        response=MagicMock(),
    )
    client = MagicMock(spec=httpx.Client)
    client.post.return_value = bad_resp

    with pytest.raises(httpx.HTTPStatusError):
        get_github_token(client=client, token_file=token_file)
