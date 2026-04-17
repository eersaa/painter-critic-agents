"""Unit tests for painter_critic.main — save_conversation_log function.

RED phase: these tests define expected behavior before implementation exists.
"""

from unittest.mock import patch


class TestSaveConversationLogUnit:
    """Unit tests for save_conversation_log(chat_history, output_dir)."""

    # --- File creation ---

    def test_main_save_log_creates_file_in_output_dir(self, tmp_output_dir):
        from painter_critic.main import save_conversation_log

        history = [{"name": "Critic", "content": "Hello", "role": "user"}]

        save_conversation_log(history, str(tmp_output_dir))

        assert (tmp_output_dir / "conversation.log").exists()

    # --- Agent names in output ---

    def test_main_save_log_contains_agent_names_from_history(self, tmp_output_dir):
        from painter_critic.main import save_conversation_log

        history = [
            {"name": "Critic", "content": "Draw something", "role": "user"},
            {"name": "Painter", "content": "I drew a circle", "role": "assistant"},
        ]

        save_conversation_log(history, str(tmp_output_dir))

        content = (tmp_output_dir / "conversation.log").read_text()
        assert "Critic" in content
        assert "Painter" in content

    # --- Multimodal content: extract text, skip image_url ---

    def test_main_save_log_extracts_text_from_multimodal_content(self, tmp_output_dir):
        from painter_critic.main import save_conversation_log

        history = [
            {
                "name": "Critic",
                "content": [
                    {"type": "text", "text": "Nice painting!"},
                    {
                        "type": "image_url",
                        "image_url": {"url": "data:image/png;base64,abc123"},
                    },
                    {"type": "text", "text": "Add more color."},
                ],
                "role": "user",
            },
        ]

        save_conversation_log(history, str(tmp_output_dir))

        content = (tmp_output_dir / "conversation.log").read_text()
        assert "Nice painting!" in content
        assert "Add more color." in content
        assert "data:image/png;base64" not in content
        assert "image_url" not in content

    # --- None content -> [tool call] ---

    def test_main_save_log_handles_none_content_as_tool_call(self, tmp_output_dir):
        from painter_critic.main import save_conversation_log

        history = [
            {"name": "Painter", "content": None, "role": "assistant"},
        ]

        save_conversation_log(history, str(tmp_output_dir))

        content = (tmp_output_dir / "conversation.log").read_text()
        assert "[tool call]" in content

    # --- String content appears as-is ---

    def test_main_save_log_handles_string_content(self, tmp_output_dir):
        from painter_critic.main import save_conversation_log

        history = [
            {"name": "Painter", "content": "I drew a red square", "role": "assistant"},
        ]

        save_conversation_log(history, str(tmp_output_dir))

        content = (tmp_output_dir / "conversation.log").read_text()
        assert "I drew a red square" in content

    # --- Creates output directory if missing ---

    def test_main_save_log_creates_output_directory_if_missing(self, tmp_output_dir):
        from painter_critic.main import save_conversation_log

        # tmp_output_dir fixture returns a non-existent path
        assert not tmp_output_dir.exists()

        history = [{"name": "Critic", "content": "Hello", "role": "user"}]

        save_conversation_log(history, str(tmp_output_dir))

        assert tmp_output_dir.exists()
        assert (tmp_output_dir / "conversation.log").exists()

    # --- Empty history creates empty file ---

    def test_main_save_log_empty_history_creates_empty_file(self, tmp_output_dir):
        from painter_critic.main import save_conversation_log

        save_conversation_log([], str(tmp_output_dir))

        log_path = tmp_output_dir / "conversation.log"
        assert log_path.exists()
        assert log_path.read_text() == ""

    # --- Message format: "--- {name} ---\n{content}\n\n" ---

    def test_main_save_log_message_format_has_name_header_and_content(
        self, tmp_output_dir
    ):
        from painter_critic.main import save_conversation_log

        history = [
            {"name": "Critic", "content": "Please draw a house", "role": "user"},
        ]

        save_conversation_log(history, str(tmp_output_dir))

        content = (tmp_output_dir / "conversation.log").read_text()
        assert "--- Critic ---" in content
        assert "Please draw a house" in content

    def test_main_save_log_multiple_messages_all_formatted(self, tmp_output_dir):
        from painter_critic.main import save_conversation_log

        history = [
            {"name": "Critic", "content": "Draw a tree", "role": "user"},
            {"name": "Painter", "content": "Done drawing", "role": "assistant"},
            {"name": "Critic", "content": "Add leaves", "role": "user"},
        ]

        save_conversation_log(history, str(tmp_output_dir))

        content = (tmp_output_dir / "conversation.log").read_text()
        assert "--- Critic ---" in content
        assert "--- Painter ---" in content
        assert "Draw a tree" in content
        assert "Done drawing" in content
        assert "Add leaves" in content

    def test_main_save_log_multimodal_text_blocks_joined(self, tmp_output_dir):
        from painter_critic.main import save_conversation_log

        history = [
            {
                "name": "Critic",
                "content": [
                    {"type": "text", "text": "First thought."},
                    {
                        "type": "image_url",
                        "image_url": {"url": "data:image/png;base64,xyz"},
                    },
                    {"type": "text", "text": "Second thought."},
                ],
                "role": "user",
            },
        ]

        save_conversation_log(history, str(tmp_output_dir))

        content = (tmp_output_dir / "conversation.log").read_text()
        # Both text blocks should be joined in the output
        assert "First thought." in content
        assert "Second thought." in content


class _FakeChatResult:
    """Minimal stand-in for autogen ChatResult."""

    def __init__(self):
        self.chat_history = []


class TestRunPipelinePhase1Message:
    """run_pipeline must send a multimodal message (text + canvas image)
    to the Painter in Phase 1 so the LLM can examine the canvas before
    issuing tool calls.
    """

    def test_run_pipeline_phase1_message_is_multimodal(self, api_url_env):
        from painter_critic import main as main_module

        captured = []

        def fake_initiate_chat(self, recipient, *args, **kwargs):
            captured.append({"sender": self, "recipient": recipient, "kwargs": kwargs})
            return _FakeChatResult()

        with patch(
            "autogen.ConversableAgent.initiate_chat",
            new=fake_initiate_chat,
        ):
            main_module.run_pipeline("a red square", rounds=1)

        assert captured, "expected initiate_chat to be called"
        phase1 = captured[0]
        message = phase1["kwargs"].get("message")

        assert isinstance(message, dict), (
            f"Phase 1 message must be a dict with 'content' list, got: {type(message).__name__}"
        )
        content = message.get("content")
        assert isinstance(content, list), (
            f"Phase 1 message['content'] must be a list, got: {type(content).__name__}"
        )

        types = [block.get("type") for block in content if isinstance(block, dict)]
        assert "image_url" in types, (
            f"Phase 1 message must include an image_url block; got types: {types}"
        )


class TestNestedChatMessage:
    """_nested_chat_message wraps the trigger message so AG2's nested
    initiate_chat accepts multimodal (list-typed) content without raising.
    """

    def test_nested_chat_message_wraps_list_content_in_dict(self):
        from painter_critic.main import _nested_chat_message

        multimodal = [
            {"type": "text", "text": "Add more red."},
            {"type": "image_url", "image_url": {"url": "data:image/png;base64,abc"}},
        ]
        messages = [{"role": "user", "content": multimodal}]

        result = _nested_chat_message(None, messages, None, None)

        assert isinstance(result, dict)
        assert result["content"] == multimodal

    def test_nested_chat_message_passes_string_content_through(self):
        from painter_critic.main import _nested_chat_message

        messages = [{"role": "user", "content": "plain feedback"}]

        result = _nested_chat_message(None, messages, None, None)

        assert result == "plain feedback"

    def test_nested_chat_message_handles_missing_content(self):
        from painter_critic.main import _nested_chat_message

        messages = [{"role": "user"}]

        result = _nested_chat_message(None, messages, None, None)

        assert result == ""
