"""Tests for agents/korean/main.py."""

from unittest.mock import MagicMock, patch
from agents.korean.main import korean_assistant
from agents.korean.config import KOREAN_ASSISTANT_SYSTEM_PROMPT, KOREAN_ASSISTANT_MODEL
from strands_tools import file_read, file_write, editor


@patch("agents.korean.main.Agent")
def test_korean_assistant_happy_path(mock_agent_class):
    # Setup mock agent instance
    mock_agent_instance = mock_agent_class.return_value
    mock_agent_instance.return_value = "Hangul response"

    query = "How to say 'apple'?"
    result = korean_assistant(query)

    # Verify Agent initialization
    mock_agent_class.assert_called_once_with(
        system_prompt=KOREAN_ASSISTANT_SYSTEM_PROMPT,
        model=KOREAN_ASSISTANT_MODEL,
        tools=[editor, file_read, file_write],
    )

    # Verify Agent call with formatted query
    expected_formatted_query = f"Answer this Korean language learning question for an English speaker who reads Hangul and is fluent in Japanese with Kanji knowledge. Use Hangul with English translation (no romanization), and draw parallels to Japanese wherever helpful: {query}"
    mock_agent_instance.assert_called_once_with(expected_formatted_query)

    assert result == "Hangul response"


@patch("agents.korean.main.Agent")
def test_korean_assistant_empty_response(mock_agent_class):
    mock_agent_instance = mock_agent_class.return_value
    mock_agent_instance.return_value = ""

    result = korean_assistant("test query")

    assert (
        "I apologize, but I couldn't properly analyze your Korean language question."
        in result
    )


@patch("agents.korean.main.Agent")
def test_korean_assistant_error(mock_agent_class):
    mock_agent_instance = mock_agent_class.return_value
    mock_agent_instance.side_effect = Exception("LLM error")

    result = korean_assistant("test query")

    assert "Error processing your Korean language query: LLM error" in result
