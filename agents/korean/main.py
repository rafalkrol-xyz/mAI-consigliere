"""Korean Assistant agent."""

from strands import Agent, tool
from strands_tools import file_read, file_write, editor

from agents.korean.config import KOREAN_ASSISTANT_SYSTEM_PROMPT, KOREAN_ASSISTANT_MODEL


@tool
def korean_assistant(query: str) -> str:
    """
    Process and respond to Korean language learning queries from English speakers.

    Args:
        query: The user's Korean language question

    Returns:
        A helpful response addressing Korean language concepts, with examples in Hangul and English (no romanization)
    """
    formatted_query = f"Answer this Korean language learning question for an English speaker who reads Hangul and is fluent in Japanese with Kanji knowledge. Use Hangul with English translation (no romanization), and draw parallels to Japanese wherever helpful: {query}"

    try:
        print("Routed to Korean Assistant")

        korean_agent = Agent(
            system_prompt=KOREAN_ASSISTANT_SYSTEM_PROMPT,
            model=KOREAN_ASSISTANT_MODEL,
            tools=[editor, file_read, file_write],
        )
        agent_response = korean_agent(formatted_query)
        text_response = str(agent_response)

        if len(text_response) > 0:
            return text_response

        return "I apologize, but I couldn't properly analyze your Korean language question. Could you please rephrase or provide more context?"
    except Exception as e:
        return f"Error processing your Korean language query: {str(e)}"
