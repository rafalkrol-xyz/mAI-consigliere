import asyncio
import webbrowser
from urllib.parse import parse_qs, urlparse

_DEFAULT_PORT = 9876
_AUTH_TIMEOUT = 120  # seconds


async def open_browser(url: str) -> None:
    """Open the system browser for OAuth login.

    Falls back to printing the URL if the browser cannot be launched.
    Runs the blocking webbrowser call in a thread so the event loop is not stalled.
    """
    print(
        f"\nOpening browser for Atlassian login...\nIf it doesn't open, visit:\n  {url}\n"
    )
    loop = asyncio.get_running_loop()
    await loop.run_in_executor(None, webbrowser.open, url)


async def local_callback(
    port: int = _DEFAULT_PORT,
    timeout: float = _AUTH_TIMEOUT,
) -> tuple[str, str | None]:
    """Spin up a one-shot HTTP server to capture the OAuth callback.

    Args:
        port: Local TCP port to listen on.  Tries the next port if occupied.
        timeout: Seconds to wait for the callback before giving up.

    Returns:
        A (code, state) tuple.

    Raises:
        TimeoutError: If no callback arrives within *timeout* seconds.
        RuntimeError: If the OAuth provider returned an error parameter or no
            authorization code was present in the callback URL.
    """
    result: dict[str, str | None] = {}
    done = asyncio.Event()

    async def handle(
        reader: asyncio.StreamReader,
        writer: asyncio.StreamWriter,
    ) -> None:
        try:
            # Read until end of HTTP headers to avoid truncation on large requests.
            raw = b""
            while b"\r\n\r\n" not in raw:
                chunk = await reader.read(4096)
                if not chunk:
                    break
                raw += chunk

            try:
                request_line = raw.decode("ascii", errors="replace").splitlines()[0]
                parts = request_line.split(" ")
                if len(parts) < 2:
                    raise ValueError(f"Malformed request line: {request_line!r}")
                path = parts[1]
            except (IndexError, ValueError):
                writer.write(
                    b"HTTP/1.1 400 Bad Request\r\nContent-Type: text/html\r\n\r\n"
                    b"<h1>Bad Request</h1>"
                )
                await writer.drain()
                return

            params = parse_qs(urlparse(path).query)

            # OAuth error from the provider (e.g. user denied access)
            if "error" in params:
                error = params["error"][0]
                result["error"] = error
                writer.write(
                    b"HTTP/1.1 400 Bad Request\r\nContent-Type: text/html\r\n\r\n"
                    b"<h1>Authentication failed. You can close this tab.</h1>"
                )
            else:
                result["code"] = params.get("code", [None])[0]
                result["state"] = params.get("state", [None])[0]
                writer.write(
                    b"HTTP/1.1 200 OK\r\nContent-Type: text/html\r\n\r\n"
                    b"<h1>Authenticated! You can close this tab.</h1>"
                )

            await writer.drain()
        finally:
            writer.close()
            await writer.wait_closed()
            done.set()

    # Let OSError propagate if the port is already in use.
    server = await asyncio.start_server(handle, "127.0.0.1", port)

    async with server:
        await server.start_serving()
        try:
            await asyncio.wait_for(done.wait(), timeout=timeout)
        except asyncio.TimeoutError:
            raise TimeoutError(
                f"No OAuth callback received within {timeout} seconds."
            ) from None

    if "error" in result:
        raise RuntimeError(f"OAuth provider returned error: {result['error']}")

    code = result.get("code")
    if code is None:
        raise RuntimeError("OAuth callback did not contain an authorization code.")

    return code, result.get("state")
