"""Tests for agents/consigliere/cli.py."""

from unittest.mock import patch

from rich.console import Console
from rich.live import Live
from rich.spinner import Spinner

from agents.consigliere.cli import RichStreamingCallbackHandler, render_banner


def _recording_console() -> Console:
    return Console(record=True, force_terminal=True, width=100)


class TestRichStreamingCallbackHandler:
    """Tests for RichStreamingCallbackHandler."""

    def test_start_shows_spinner_and_no_streaming(self) -> None:
        handler = RichStreamingCallbackHandler(_recording_console())

        handler.start()

        assert handler._live is not None
        assert isinstance(handler._live, Live)
        assert isinstance(handler._live.get_renderable(), Spinner)
        assert handler._streaming is False
        assert handler._buffer == ""

        handler.stop()

    def test_call_ignored_when_not_started(self) -> None:
        handler = RichStreamingCallbackHandler(_recording_console())

        handler(data="hello")

        assert handler._buffer == ""
        assert handler._streaming is False

    def test_call_ignored_when_data_missing_or_empty(self) -> None:
        handler = RichStreamingCallbackHandler(_recording_console())
        handler.start()

        handler()
        handler(data="")

        assert handler._buffer == ""
        assert handler._streaming is False

        handler.stop()

    def test_call_appends_data_and_marks_streaming(self) -> None:
        handler = RichStreamingCallbackHandler(_recording_console())
        handler.start()

        handler(data="Hello, ")
        handler(data="world!")

        assert handler._buffer == "Hello, world!"
        assert handler._streaming is True

        handler.stop()

    def test_stop_clears_live_and_streaming_state(self) -> None:
        handler = RichStreamingCallbackHandler(_recording_console())
        handler.start()
        handler(data="some tokens")

        handler.stop()

        assert handler._live is None
        assert handler._streaming is False

    def test_stop_without_start_is_a_noop(self) -> None:
        handler = RichStreamingCallbackHandler(_recording_console())

        handler.stop()

        assert handler._live is None

    def test_start_resets_buffer_from_previous_turn(self) -> None:
        handler = RichStreamingCallbackHandler(_recording_console())
        handler.start()
        handler(data="leftover from previous turn")
        handler.stop()

        handler.start()

        assert handler._buffer == ""
        assert handler._streaming is False

        handler.stop()


class TestRenderBanner:
    """Tests for render_banner()."""

    @patch("agents.consigliere.cli.os.getcwd", return_value="/home/user/project")
    def test_renders_panel_with_model_id_and_cwd(self, mock_getcwd) -> None:
        console = _recording_console()

        render_banner(console)

        rendered = console.export_text()
        assert "mAI Consigliere" in rendered
        assert "/home/user/project" in rendered
        assert "exit" in rendered

    def test_renders_configured_model_id(self) -> None:
        console = _recording_console()

        with patch("agents.consigliere.cli.CONSIGLIERE_MODEL") as mock_model:
            mock_model.config = {"model_id": "eu.anthropic.claude-sonnet-5"}
            render_banner(console)

        rendered = console.export_text()
        assert "eu.anthropic.claude-sonnet-5" in rendered

    def test_falls_back_to_unknown_when_model_id_missing(self) -> None:
        console = _recording_console()

        with patch("agents.consigliere.cli.CONSIGLIERE_MODEL") as mock_model:
            mock_model.config = {}
            render_banner(console)

        rendered = console.export_text()
        assert "unknown" in rendered
