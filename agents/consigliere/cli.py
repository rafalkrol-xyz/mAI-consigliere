"""Rich-based rendering for the mAI Consigliere CLI."""

import os
from typing import Any

from rich.console import Console
from rich.live import Live
from rich.markdown import Markdown
from rich.panel import Panel
from rich.spinner import Spinner
from rich.text import Text

from agents.consigliere.config import CONSIGLIERE_MODEL


class RichStreamingCallbackHandler:
    """Strands callback handler that streams tokens into a Rich Live block.

    Shows a spinner until the first token arrives, then paints the response
    incrementally as Markdown so tables, bullets, and code fences render
    while the model is still generating.
    """

    def __init__(self, console: Console) -> None:
        self._console = console
        self._buffer = ""
        self._live: Live | None = None
        self._streaming = False

    def start(self) -> None:
        self._buffer = ""
        self._streaming = False
        self._live = Live(
            Spinner("dots", text=Text(" Thinking…", style="dim")),
            console=self._console,
            refresh_per_second=12,
            transient=False,
        )
        self._live.start()

    def stop(self) -> None:
        if self._live is not None:
            self._live.stop()
            self._live = None
            self._streaming = False

    def __call__(self, **kwargs: Any) -> None:
        data = kwargs.get("data", "")
        if not data or self._live is None:
            return
        self._buffer += data
        self._streaming = True
        self._live.update(Markdown(self._buffer))


def render_banner(console: Console) -> None:
    model_id = CONSIGLIERE_MODEL.config.get("model_id", "unknown")
    body = Text.from_markup(
        "[bold cyan]mAI Consigliere[/bold cyan]\n\n"
        f"[dim]Model:[/dim] {model_id}\n"
        f"[dim]Cwd  :[/dim] {os.getcwd()}\n\n"
        "[dim]Ask a question in any subject area — I'll route it to the right specialist.[/dim]\n"
        "[dim]Type 'exit' to quit.[/dim]"
    )
    console.print(Panel(body, border_style="cyan", padding=(1, 2)))
