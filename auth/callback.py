import webbrowser

async def _open_browser(url: str) -> None:
    print(f"\nOpening browser for Atlassian login...\nIf it doesn't open, visit:\n  {url}\n")
    webbrowser.open(url)


async def _local_callback() -> tuple[str, str | None]:
    """Spin up a one-shot HTTP server to capture the OAuth callback."""
    import asyncio
    from urllib.parse import parse_qs, urlparse

    result: dict = {}
    done = asyncio.Event()

    async def handle(reader: asyncio.StreamReader, writer: asyncio.StreamWriter) -> None:
        data = await reader.read(4096)
        request_line = data.decode().splitlines()[0]
        path = request_line.split(" ")[1]
        params = parse_qs(urlparse(path).query)
        result["code"] = params.get("code", [None])[0]
        result["state"] = params.get("state", [None])[0]
        writer.write(b"HTTP/1.1 200 OK\r\nContent-Type: text/html\r\n\r\n<h1>Authenticated! You can close this tab.</h1>")
        await writer.drain()
        writer.close()
        done.set()

    server = await asyncio.start_server(handle, "localhost", 9876)
    async with server:
        await done.wait()

    return result["code"], result.get("state")
