"""Main logic for the mAI Consigliere orchestrator."""

import readline  # noqa: F401 — enables line-editing & history in input()
from typing import Any

from rich.console import Console

from strands import Agent

from agents.consigliere.cli import RichStreamingCallbackHandler, render_banner
from agents.consigliere.config import CONSIGLIERE_AGENT_PROMPT, CONSIGLIERE_MODEL
from agents.github import github_assistant
from agents.jira import jira_assistant
from agents.korean import korean_assistant


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


def run_app() -> None:
    """Run the interactive mAI Consigliere application loop."""
    console = Console()
    handler = RichStreamingCallbackHandler(console)
    consigliere = create_consigliere(callback_handler=handler)

    render_banner(console)

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
