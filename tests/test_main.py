"""Unit tests for painter_critic.main — save_conversation_log function.

RED phase: these tests define expected behavior before implementation exists.
"""

import pytest
from unittest.mock import patch


class TestSaveConversationLogUnit:
    """Unit tests for save_conversation_log(chat_history, output_dir)."""

    # --- File creation ---

    def test_main_save_log_creates_file_in_output_dir(self, tmp_output_dir):
        from painter_critic.main import save_conversation_log

        history = [{"name": "Critic", "content": "Hello", "role": "user"}]

        save_conversation_log(history, str(tmp_output_dir), "x")

        assert (tmp_output_dir / "conversation.log").exists()

    # --- Agent names in output ---

    def test_main_save_log_contains_agent_names_from_history(self, tmp_output_dir):
        from painter_critic.main import save_conversation_log

        history = [
            {"name": "Critic", "content": "Draw something", "role": "user"},
            {"name": "Painter", "content": "I drew a circle", "role": "assistant"},
        ]

        save_conversation_log(history, str(tmp_output_dir), "x")

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

        save_conversation_log(history, str(tmp_output_dir), "x")

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

        save_conversation_log(history, str(tmp_output_dir), "x")

        content = (tmp_output_dir / "conversation.log").read_text()
        assert "[tool call]" in content

    # --- String content appears as-is ---

    def test_main_save_log_handles_string_content(self, tmp_output_dir):
        from painter_critic.main import save_conversation_log

        history = [
            {"name": "Painter", "content": "I drew a red square", "role": "assistant"},
        ]

        save_conversation_log(history, str(tmp_output_dir), "x")

        content = (tmp_output_dir / "conversation.log").read_text()
        assert "I drew a red square" in content

    # --- Creates output directory if missing ---

    def test_main_save_log_creates_output_directory_if_missing(self, tmp_output_dir):
        from painter_critic.main import save_conversation_log

        # tmp_output_dir fixture returns a non-existent path
        assert not tmp_output_dir.exists()

        history = [{"name": "Critic", "content": "Hello", "role": "user"}]

        save_conversation_log(history, str(tmp_output_dir), "x")

        assert tmp_output_dir.exists()
        assert (tmp_output_dir / "conversation.log").exists()

    # --- Empty history still emits User header ---

    def test_main_save_log_empty_history_contains_only_user_header(
        self, tmp_output_dir
    ):
        from painter_critic.main import save_conversation_log

        save_conversation_log([], str(tmp_output_dir), "a red square")

        log_path = tmp_output_dir / "conversation.log"
        assert log_path.exists()
        assert log_path.read_text() == "--- User ---\nPaint: a red square\n\n"

    # --- Message format: "--- {name} ---\n{content}\n\n" ---

    def test_main_save_log_message_format_has_name_header_and_content(
        self, tmp_output_dir
    ):
        from painter_critic.main import save_conversation_log

        history = [
            {"name": "Critic", "content": "Please draw a house", "role": "user"},
        ]

        save_conversation_log(history, str(tmp_output_dir), "x")

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

        save_conversation_log(history, str(tmp_output_dir), "x")

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

        save_conversation_log(history, str(tmp_output_dir), "x")

        content = (tmp_output_dir / "conversation.log").read_text()
        # Both text blocks should be joined in the output
        assert "First thought." in content
        assert "Second thought." in content

    # --- User prompt header prepended to log ---

    def test_main_save_log_prepends_user_header_when_prompt_given(self, tmp_output_dir):
        from painter_critic.main import save_conversation_log

        history = [{"name": "Painter", "content": "done", "role": "assistant"}]

        save_conversation_log(history, str(tmp_output_dir), "a red square")

        content = (tmp_output_dir / "conversation.log").read_text()
        assert "--- User ---" in content
        assert "Paint: a red square" in content

    def test_main_save_log_user_header_precedes_chat_history(self, tmp_output_dir):
        from painter_critic.main import save_conversation_log

        history = [{"name": "Painter", "content": "done", "role": "assistant"}]

        save_conversation_log(history, str(tmp_output_dir), "a red square")

        content = (tmp_output_dir / "conversation.log").read_text()
        assert content.index("--- User ---") < content.index("--- Painter ---")

    def test_main_save_log_prompt_is_required_positional_arg(self, tmp_output_dir):
        from painter_critic.main import save_conversation_log

        with pytest.raises(TypeError):
            save_conversation_log([], str(tmp_output_dir))


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


class TestSetupPipelineHookWiring:
    """Pin the hook ordering on process_all_messages_before_reply for both
    agents: strip-assistant → prune-stale-user → reply. Ordering is
    load-bearing — reply must run last so the attached image survives pruning."""

    @pytest.fixture()
    def pipeline(self, api_url_env):
        from painter_critic.main import setup_pipeline

        painter, executor, critic, canvas, tools, tracker = setup_pipeline("test")
        return painter, executor, critic, canvas, tools, tracker

    def _run_chain(self, agent, messages):
        result = messages
        for hook in agent.hook_lists["process_all_messages_before_reply"]:
            result = hook(result)
        return result

    def test_setup_pipeline_painter_pre_reply_chain_has_three_hooks(self, pipeline):
        painter, *_ = pipeline

        assert len(painter.hook_lists["process_all_messages_before_reply"]) == 3

    def test_setup_pipeline_critic_pre_reply_chain_has_three_hooks(self, pipeline):
        _, _, critic, *_ = pipeline

        assert len(critic.hook_lists["process_all_messages_before_reply"]) == 3

    def test_setup_pipeline_painter_chain_strips_assistant_images(self, pipeline):
        painter, _, _, canvas, *_ = pipeline
        image = canvas.to_image_content()
        messages = [
            {"role": "assistant", "content": [{"type": "text", "text": "r"}, image]},
            {"role": "user", "content": [{"type": "text", "text": "u"}, image]},
        ]

        result = self._run_chain(painter, messages)

        assistant_types = [b["type"] for b in result[0]["content"]]
        assert "image_url" not in assistant_types

    def test_setup_pipeline_painter_chain_prunes_stale_user_images(self, pipeline):
        painter, _, _, canvas, *_ = pipeline
        image = canvas.to_image_content()
        messages = [
            {"role": "user", "content": [{"type": "text", "text": "old"}, image]},
            {"role": "user", "content": [{"type": "text", "text": "new"}, image]},
        ]

        result = self._run_chain(painter, messages)

        first_types = [b["type"] for b in result[0]["content"]]
        assert "image_url" not in first_types

    def test_setup_pipeline_painter_chain_last_message_carries_current_canvas(
        self, pipeline
    ):
        painter, _, _, canvas, *_ = pipeline
        messages = [{"role": "user", "content": "ping"}]

        result = self._run_chain(painter, messages)

        last_content = result[-1]["content"]
        assert isinstance(last_content, list)
        image_blocks = [b for b in last_content if b.get("type") == "image_url"]
        assert len(image_blocks) == 1
        assert image_blocks[0] == canvas.to_image_content()

    def test_setup_pipeline_critic_chain_last_message_carries_current_canvas(
        self, pipeline
    ):
        _, _, critic, canvas, *_ = pipeline
        messages = [{"role": "user", "content": "ping"}]

        result = self._run_chain(critic, messages)

        last_content = result[-1]["content"]
        assert isinstance(last_content, list)
        image_blocks = [b for b in last_content if b.get("type") == "image_url"]
        assert len(image_blocks) == 1
        assert image_blocks[0] == canvas.to_image_content()
