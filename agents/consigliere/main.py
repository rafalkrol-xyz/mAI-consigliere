"""Main logic for the mAI Consigliere orchestrator."""

from strands import Agent
from agents.consigliere.config import CONSIGLIERE_MODEL, CONSIGLIERE_AGENT_PROMPT
from agents.korean import korean_assistant
from agents.github import github_assistant
from agents.jira import jira_assistant


def create_consigliere() -> Agent:
    """Create the mAI Consigliere orchestrator agent."""
    return Agent(
        system_prompt=CONSIGLIERE_AGENT_PROMPT,
        callback_handler=None,
        model=CONSIGLIERE_MODEL,
        tools=[
            korean_assistant,
            github_assistant,
            jira_assistant,
        ],
    )


def run_app():
    """Run the interactive mAI Consigliere application loop."""
    consigliere = create_consigliere()

    print(
        "Ask a question in any subject area, and I'll route it to the appropriate specialist."
    )
    print("Type 'exit' to quit.")

    while True:
        try:
            user_input = input("\n> ")
            if user_input.lower() == "exit":
                print("\nGoodbye! 👋")
                break

            response = consigliere(
                user_input,
            )

            # Extract and print only the relevant content from the specialized agent's response
            content = str(response)
            print(content)

        except KeyboardInterrupt:
            print("\n\nExecution interrupted. Exiting...")
            break
        except Exception as e:
            print(f"\nAn error occurred: {str(e)}")
            print("Please try asking a different question.")
