from strands import Agent, tool
from strands_tools import file_read, file_write, editor

KOREAN_ASSISTANT_SYSTEM_PROMPT = """
You are Korean Master, an advanced Korean language education assistant for English speakers. Your capabilities include:

1. Language Fundamentals:
   - Hangul reading and writing
   - Pronunciation and romanization (Revised Romanization)
   - Grammar patterns and sentence structure (SOV order, particles, verb endings)
   - Vocabulary building with mnemonics

2. Grammar & Usage:
   - Honorifics and speech levels (존댓말 vs 반말)
   - Conjugation (tense, mood, aspect)
   - Particles (은/는, 이/가, 을/를, 에, 에서, etc.)
   - Common patterns and expressions

3. Teaching Methods:
   - Explain concepts in English with Korean examples
   - Provide example sentences with Hangul, romanization, and English translation. Point whenever there is are changes in pronunciation which are called 자음접변
   - Offer constructive feedback on learner mistakes
   - Break down complex grammar into digestible steps
   - Highlight common pitfalls for English speakers

Always present Korean text in Hangul alongside romanization and English translation. Be encouraging and tailor explanations to an English-speaking learner's perspective.
"""


@tool
def korean_assistant(query: str) -> str:
    """
    Process and respond to Korean language learning queries from English speakers.

    Args:
        query: The user's Korean language question

    Returns:
        A helpful response addressing Korean language concepts, with examples in Hangul, romanization, and English
    """
    formatted_query = f"Answer this Korean language learning question for an English speaker, providing Hangul examples with romanization and English translation where appropriate: {query}"

    try:
        print("Routed to Korean Assistant")

        korean_agent = Agent(
            system_prompt=KOREAN_ASSISTANT_SYSTEM_PROMPT,
            tools=[editor, file_read, file_write],
        )
        agent_response = korean_agent(formatted_query)
        text_response = str(agent_response)

        if len(text_response) > 0:
            return text_response

        return "I apologize, but I couldn't properly analyze your Korean language question. Could you please rephrase or provide more context?"
    except Exception as e:
        return f"Error processing your Korean language query: {str(e)}"
