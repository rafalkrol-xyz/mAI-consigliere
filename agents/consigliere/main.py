"""Main logic for the mAI Consigliere orchestrator."""

import os
import readline  # noqa: F401 — enables line-editing & history in input()
from typing import Any

from rich.console import Console
from rich.live import Live
from rich.markdown import Markdown
from rich.panel import Panel
from rich.spinner import Spinner
from rich.text import Text

from strands import Agent

from agents.consigliere.config import CONSIGLIERE_AGENT_PROMPT, CONSIGLIERE_MODEL
from agents.github import github_assistant
from agents.jira import jira_assistant
from agents.korean import korean_assistant


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


def create_consigliere(callback_handler: Any = None) -> Agent:
    """Create the mAI Consigliere orchestrator agent."""
    return Agent(
        system_prompt=CONSIGLIERE_AGENT_PROMPT,
        callback_handler=callback_handler,
        model=CONSIGLIERE_MODEL,
        tools=[
            korean_assistant,
            github_assistant,
            jira_assistant,
        ],
    )


def _render_banner(console: Console) -> None:
    model_id = CONSIGLIERE_MODEL.config.get("model_id", "unknown")
    body = Text.from_markup(
        "[bold cyan]mAI Consigliere[/bold cyan]\n\n"
        f"[dim]Model:[/dim] {model_id}\n"
        f"[dim]Cwd  :[/dim] {os.getcwd()}\n\n"
        "[dim]Ask a question in any subject area — I'll route it to the right specialist.[/dim]\n"
        "[dim]Type 'exit' to quit.[/dim]"
    )
    console.print(Panel(body, border_style="cyan", padding=(1, 2)))


def run_app() -> None:
    """Run the interactive mAI Consigliere application loop."""
    console = Console()
    handler = RichStreamingCallbackHandler(console)
    consigliere = create_consigliere(callback_handler=handler)

    _render_banner(console)

    while True:
        try:
            user_input = input("\n> ")
            if user_input.lower() == "exit":
                console.print("\n[bold]Goodbye! 👋[/bold]")
                break

            if not user_input.strip():
                continue

            handler.start()
            try:
                consigliere(user_input)
            finally:
                handler.stop()

        except KeyboardInterrupt:
            console.print("\n\n[yellow]Execution interrupted. Exiting…[/yellow]")
            break
        except Exception as e:
            console.print(f"\n[red]An error occurred:[/red] {e}")
            console.print("[dim]Please try asking a different question.[/dim]")
