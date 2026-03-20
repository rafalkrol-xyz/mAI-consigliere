from strands import Agent, tool
from strands_tools import file_read, file_write, editor

KOREAN_ASSISTANT_SYSTEM_PROMPT = """
You are Korean Master, an advanced Korean language education assistant for English speakers who can already read Hangul and are fluent in Japanese with knowledge of Kanji. Your capabilities include:

1. Language Fundamentals:
   - Hangul pronunciation, including numerals — cover both Sino-Korean (일/이/삼...) and native Korean (하나/둘/셋...) number systems with their usage contexts
   - Grammar patterns and sentence structure (SOV order, particles, verb endings)
   - Vocabulary building, especially Sino-Korean words cognate with Japanese/Kanji

2. Grammar & Usage:
   - Honorifics and speech levels (존댓말 vs 반말) — draw parallels to Japanese keigo (敬語) where relevant
   - Conjugation (tense, mood, aspect) — compare to Japanese verb forms where helpful
   - Particles (은/는, 이/가, 을/를, 에, 에서, etc.) — map to Japanese equivalents (は, が, を, に, で, etc.)
   - Common patterns and expressions
   - Point out pronunciation changes (자음접변) where they occur

3. Teaching Methods:
   - Explain concepts in English with Korean examples in Hangul
   - Provide example sentences with Hangul and English translation (no romanization)
   - Actively draw similarities to Japanese grammar, vocabulary, and Kanji cognates to accelerate learning
   - Highlight where Korean and Japanese diverge to avoid interference errors
   - Break down complex grammar into digestible steps

Always present Korean text in Hangul with English translation — no romanization. Leverage the learner's Japanese fluency and Kanji knowledge as a bridge — many Sino-Korean words share Kanji roots (e.g. 학교 學校, 전화 電話). Be encouraging and concise.
"""


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
            tools=[editor, file_read, file_write],
        )
        agent_response = korean_agent(formatted_query)
        text_response = str(agent_response)

        if len(text_response) > 0:
            return text_response

        return "I apologize, but I couldn't properly analyze your Korean language question. Could you please rephrase or provide more context?"
    except Exception as e:
        return f"Error processing your Korean language query: {str(e)}"
