"""Rich-based rendering for the mAI Consigliere CLI."""

import os
import time
from collections.abc import Iterator
from contextlib import contextmanager
from typing import Any

from rich.console import Console, ConsoleOptions, RenderResult
from rich.live import Live
from rich.markdown import Markdown
from rich.panel import Panel
from rich.spinner import Spinner
from rich.table import Table
from rich.text import Text

from agents.consigliere.config import CONSIGLIERE_MODEL


class ThinkingIndicator:
    """A spinner paired with an elapsed-time counter.

    Rich's Live re-renders the current renderable on every refresh tick, so
    recomputing the elapsed time in __rich_console__ is enough to animate it.
    """

    def __init__(self) -> None:
        self._start_time = time.monotonic()
        self._spinner = Spinner("dots", style="dim")

    def __rich_console__(self, console: Console, options: ConsoleOptions) -> RenderResult:
        elapsed = time.monotonic() - self._start_time
        table = Table.grid(padding=(0, 1))
        table.add_row(self._spinner, Text(f"Thinking… ({elapsed:0.1f}s)", style="dim"))
        yield table


class RichStreamingCallbackHandler:
    """Strands callback handler that streams tokens into a Rich Live block.

    Shows a spinner with an elapsed-time counter until the first token
    arrives, then paints the response incrementally as Markdown so tables,
    bullets, and code fences render while the model is still generating.
    """

    def __init__(self, console: Console) -> None:
        self._console = console
        self._buffer = ""
        self._live: Live | None = None
        self._streaming = False
        self._active = False  # True between start() and stop(), even while paused

    def start(self) -> None:
        """Begin a turn: show the thinking indicator in a fresh Live block."""
        self._buffer = ""
        self._streaming = False
        self._active = True
        self._start_live()

    def stop(self) -> None:
        """End the turn, leaving the final rendered response on screen."""
        self._active = False
        self._stop_live()
        self._streaming = False

    @contextmanager
    def paused(self) -> Iterator[None]:
        """Suspend live rendering so the terminal can take direct user input.

        Text streamed so far stays on screen; a bare spinner is erased.
        Rendering resumes with a fresh thinking indicator afterwards.
        """
        if self._live is None:
            yield
            return
        # Only erase the region if it holds nothing but the spinner.
        self._live.transient = not self._streaming
        self._stop_live()
        self._buffer = ""
        self._streaming = False
        try:
            yield
        finally:
            if self._active:
                self._start_live()

    def _start_live(self) -> None:
        self._live = Live(
            ThinkingIndicator(),
            console=self._console,
            refresh_per_second=12,
            transient=False,
        )
        self._live.start()

    def _stop_live(self) -> None:
        if self._live is not None:
            self._live.stop()
            self._live = None

    def __call__(self, **kwargs: Any) -> None:
        data = kwargs.get("data", "")
        if not data or not self._active:
            return
        self._buffer += data
        self._streaming = True
        if self._live is not None:
            self._live.update(Markdown(self._buffer))

def render_banner(console: Console) -> None:
    model_id = CONSIGLIERE_MODEL.config.get("model_id", "unknown")
    body = Text.from_markup(
        "[bold cyan]mAI Consigliere[/bold cyan]\n\n"
        f"[dim]Model:[/dim] {model_id}\n"
        f"[dim]Cwd  :[/dim] {os.getcwd()}\n\n"
        "[dim]Ask a question in any subject area — I'll route it to the right specialist.[/dim]\n"
        "[dim]Type '/help' for commands, or 'exit' to quit.[/dim]"
    )
    console.print(Panel(body, border_style="cyan", padding=(1, 2)))


def render_help(console: Console) -> None:
    body = Text.from_markup(
        "[bold cyan]Commands[/bold cyan]\n\n"
        "[dim]/help[/dim]  Show this message\n"
        "[dim]exit [/dim]  Quit mAI Consigliere"
    )
    console.print(Panel(body, border_style="cyan", padding=(1, 2)))
