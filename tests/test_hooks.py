import copy

from painter_critic.canvas import Canvas
from painter_critic.hooks import (
    RoundTracker,
    create_prune_stale_user_images_hook,
    create_reply_hook,
    create_save_hook,
    create_send_hook,
    create_strip_assistant_images_hook,
)


class TestRoundTrackerUnit:
    def test_round_tracker_initial_current_round_equals_one(self):
        tracker = RoundTracker()

        assert tracker.current_round == 1

    def test_round_tracker_increment_advances_by_one(self):
        tracker = RoundTracker()

        tracker.increment()

        assert tracker.current_round == 2

    def test_round_tracker_multiple_increments_accumulate(self):
        tracker = RoundTracker()

        tracker.increment()
        tracker.increment()
        tracker.increment()

        assert tracker.current_round == 4

    def test_round_tracker_get_image_path_format_zero_padded(self):
        tracker = RoundTracker()

        path = tracker.get_image_path("output")

        assert path == "output/round_01.png"

    def test_round_tracker_get_image_path_round_nine_pads_to_two_digits(self):
        tracker = RoundTracker()
        for _ in range(8):
            tracker.increment()

        path = tracker.get_image_path("output")

        assert path == "output/round_09.png"

    def test_round_tracker_get_image_path_double_digit_no_extra_padding(self):
        tracker = RoundTracker()
        for _ in range(14):
            tracker.increment()

        path = tracker.get_image_path("output")

        assert path == "output/round_15.png"

    def test_round_tracker_get_image_path_uses_given_directory(self):
        tracker = RoundTracker()

        path = tracker.get_image_path("results/images")

        assert path == "results/images/round_01.png"


class TestSendHookUnit:
    # -- Returns callable --

    def test_send_hook_returns_callable(self):
        canvas = Canvas()

        hook = create_send_hook(canvas)

        assert callable(hook)

    # -- String message -> multimodal --

    def test_send_hook_string_message_returns_dict_with_content_list(self):
        canvas = Canvas()
        hook = create_send_hook(canvas)

        result = hook("painter", "Draw a circle", "critic", False)

        assert isinstance(result, dict)
        assert isinstance(result["content"], list)

    def test_send_hook_string_message_text_block_preserves_original_text(self):
        canvas = Canvas()
        hook = create_send_hook(canvas)

        result = hook("painter", "Draw a circle", "critic", False)
        text_blocks = [b for b in result["content"] if b["type"] == "text"]

        assert len(text_blocks) == 1
        assert text_blocks[0]["text"] == "Draw a circle"

    def test_send_hook_string_message_includes_image_block(self):
        canvas = Canvas()
        hook = create_send_hook(canvas)

        result = hook("painter", "Draw a circle", "critic", False)
        image_blocks = [b for b in result["content"] if b["type"] == "image_url"]

        assert len(image_blocks) == 1

    # -- Dict message -> multimodal --

    def test_send_hook_dict_message_converts_content_to_list(self):
        canvas = Canvas()
        hook = create_send_hook(canvas)
        msg = {"content": "Hello", "role": "user"}

        result = hook("painter", msg, "Critic", False)

        assert isinstance(result["content"], list)

    def test_send_hook_dict_message_preserves_role_field(self):
        canvas = Canvas()
        hook = create_send_hook(canvas)
        msg = {"content": "Hello", "role": "user"}

        result = hook("painter", msg, "Critic", False)

        assert result["role"] == "user"

    def test_send_hook_dict_message_preserves_other_fields(self):
        canvas = Canvas()
        hook = create_send_hook(canvas)
        msg = {"content": "Hello", "role": "assistant", "name": "painter"}

        result = hook("painter", msg, "Critic", False)

        assert result["name"] == "painter"

    # -- Guard: tool_calls --

    def test_send_hook_dict_with_tool_calls_returns_unchanged(self):
        canvas = Canvas()
        hook = create_send_hook(canvas)
        msg = {"content": "call", "tool_calls": [{"id": "1"}]}

        result = hook("painter", msg, "Critic", False)

        assert result == msg

    # -- Guard: role=tool --

    def test_send_hook_dict_with_role_tool_returns_unchanged(self):
        canvas = Canvas()
        hook = create_send_hook(canvas)
        msg = {"content": "result", "role": "tool"}

        result = hook("painter", msg, "Critic", False)

        assert result == msg

    # -- Image block format --

    def test_send_hook_image_block_has_correct_format(self):
        canvas = Canvas()
        hook = create_send_hook(canvas)

        result = hook("painter", "text", "critic", False)
        image_blocks = [b for b in result["content"] if b["type"] == "image_url"]
        image_block = image_blocks[0]

        assert "image_url" in image_block
        assert image_block["image_url"]["url"].startswith("data:image/png;base64,")

    def test_send_hook_image_block_matches_canvas_to_image_content(self):
        canvas = Canvas()
        hook = create_send_hook(canvas)
        expected = canvas.to_image_content()

        result = hook("painter", "text", "critic", False)
        image_blocks = [b for b in result["content"] if b["type"] == "image_url"]

        assert image_blocks[0] == expected

    # -- Already-multimodal content --

    def test_send_hook_list_content_appends_image_block(self):
        canvas = Canvas()
        hook = create_send_hook(canvas)
        msg = {"content": [{"type": "text", "text": "existing"}]}

        result = hook("painter", msg, "Critic", False)

        assert len(result["content"]) == 2
        assert result["content"][0] == {"type": "text", "text": "existing"}
        assert result["content"][1]["type"] == "image_url"

    # -- Does not mutate original dict --

    def test_send_hook_does_not_mutate_original_dict(self):
        canvas = Canvas()
        hook = create_send_hook(canvas)
        msg = {"content": "Hello", "role": "user"}
        original = copy.deepcopy(msg)

        hook("painter", msg, "Critic", False)

        assert msg == original


class TestReplyHookUnit:
    # -- Returns callable --

    def test_reply_hook_returns_callable(self):
        canvas = Canvas()

        hook = create_reply_hook(canvas)

        assert callable(hook)

    # -- Injects into last message --

    def test_reply_hook_last_message_content_becomes_list(self):
        canvas = Canvas()
        hook = create_reply_hook(canvas)
        messages = [
            {"content": "first", "role": "user"},
            {"content": "second", "role": "assistant"},
        ]

        result = hook(messages)

        assert isinstance(result[-1]["content"], list)

    def test_reply_hook_last_message_contains_image_block(self):
        canvas = Canvas()
        hook = create_reply_hook(canvas)
        messages = [{"content": "hello", "role": "user"}]

        result = hook(messages)
        image_blocks = [b for b in result[-1]["content"] if b["type"] == "image_url"]

        assert len(image_blocks) == 1

    # -- Preserves message count --

    def test_reply_hook_preserves_message_count(self):
        canvas = Canvas()
        hook = create_reply_hook(canvas)
        messages = [
            {"content": "a", "role": "user"},
            {"content": "b", "role": "assistant"},
            {"content": "c", "role": "user"},
        ]

        result = hook(messages)

        assert len(result) == 3

    # -- Does not modify earlier messages --

    def test_reply_hook_earlier_messages_unchanged(self):
        canvas = Canvas()
        hook = create_reply_hook(canvas)
        messages = [
            {"content": "first", "role": "user"},
            {"content": "second", "role": "assistant"},
            {"content": "third", "role": "user"},
        ]

        result = hook(messages)

        assert result[0]["content"] == "first"
        assert result[1]["content"] == "second"

    # -- Guard: last message has tool_calls --

    def test_reply_hook_skips_when_last_has_tool_calls(self):
        canvas = Canvas()
        hook = create_reply_hook(canvas)
        messages = [
            {"content": "hi", "role": "user"},
            {"content": "call", "role": "assistant", "tool_calls": [{"id": "1"}]},
        ]

        result = hook(messages)

        assert result[-1]["content"] == "call"
        assert isinstance(result[-1]["content"], str)

    # -- Guard: last message has role=tool --

    def test_reply_hook_skips_when_last_has_role_tool(self):
        canvas = Canvas()
        hook = create_reply_hook(canvas)
        messages = [
            {"content": "hi", "role": "user"},
            {"content": "result", "role": "tool"},
        ]

        result = hook(messages)

        assert result[-1]["content"] == "result"
        assert isinstance(result[-1]["content"], str)

    # -- Empty list --

    def test_reply_hook_empty_list_returns_empty(self):
        canvas = Canvas()
        hook = create_reply_hook(canvas)

        result = hook([])

        assert result == []

    # -- Image reflects current canvas state --

    def test_reply_hook_image_reflects_drawn_canvas_state(self):
        canvas = Canvas()
        hook = create_reply_hook(canvas)
        messages = [{"content": "check", "role": "user"}]

        blank_result = hook(messages)
        blank_image = [
            b for b in blank_result[-1]["content"] if b["type"] == "image_url"
        ][0]

        draw = canvas.draw()
        draw.rectangle([0, 0, 100, 100], fill="red")

        drawn_result = hook(messages)
        drawn_image = [
            b for b in drawn_result[-1]["content"] if b["type"] == "image_url"
        ][0]

        assert blank_image != drawn_image


class TestSaveHookUnit:
    # -- Returns callable --

    def test_save_hook_returns_callable(self):
        canvas = Canvas()
        tracker = RoundTracker()

        hook = create_save_hook(canvas, tracker, "output")

        assert callable(hook)

    # -- Non-tool message: saves file --

    def test_save_hook_non_tool_message_saves_file(self, tmp_output_dir):
        canvas = Canvas()
        tracker = RoundTracker()
        hook = create_save_hook(canvas, tracker, str(tmp_output_dir))
        msg = {"content": "Nice painting", "role": "assistant"}

        hook("painter", msg, "Critic", False)

        expected_path = tmp_output_dir / "round_01.png"
        assert expected_path.exists()

    # -- Non-tool message: increments tracker --

    def test_save_hook_non_tool_message_increments_tracker(self, tmp_output_dir):
        canvas = Canvas()
        tracker = RoundTracker()
        hook = create_save_hook(canvas, tracker, str(tmp_output_dir))
        msg = {"content": "Nice painting", "role": "assistant"}

        hook("painter", msg, "Critic", False)

        assert tracker.current_round == 2

    # -- Non-tool message: returns original message unchanged --

    def test_save_hook_non_tool_message_returns_message_unchanged(self, tmp_output_dir):
        canvas = Canvas()
        tracker = RoundTracker()
        hook = create_save_hook(canvas, tracker, str(tmp_output_dir))
        msg = {"content": "Nice painting", "role": "assistant"}

        result = hook("painter", msg, "Critic", False)

        assert result is msg

    # -- Successive calls save to incrementing paths --

    def test_save_hook_successive_calls_save_incrementing_filenames(
        self, tmp_output_dir
    ):
        canvas = Canvas()
        tracker = RoundTracker()
        hook = create_save_hook(canvas, tracker, str(tmp_output_dir))
        msg = {"content": "text", "role": "assistant"}

        hook("painter", msg, "Critic", False)
        hook("painter", msg, "Critic", False)

        assert (tmp_output_dir / "round_01.png").exists()
        assert (tmp_output_dir / "round_02.png").exists()

    # -- Guard: tool_calls message --

    def test_save_hook_tool_calls_message_no_file_written(self, tmp_output_dir):
        canvas = Canvas()
        tracker = RoundTracker()
        hook = create_save_hook(canvas, tracker, str(tmp_output_dir))
        msg = {"content": "call", "tool_calls": [{"id": "1"}]}

        result = hook("painter", msg, "Critic", False)

        assert not tmp_output_dir.exists()
        assert tracker.current_round == 1
        assert result is msg

    # -- Guard: role=tool message --

    def test_save_hook_role_tool_message_no_file_written(self, tmp_output_dir):
        canvas = Canvas()
        tracker = RoundTracker()
        hook = create_save_hook(canvas, tracker, str(tmp_output_dir))
        msg = {"content": "result", "role": "tool"}

        result = hook("painter", msg, "Critic", False)

        assert not tmp_output_dir.exists()
        assert tracker.current_round == 1
        assert result is msg

    # -- Saved file is valid PNG --

    def test_save_hook_saved_file_is_valid_png(self, tmp_output_dir):
        canvas = Canvas()
        tracker = RoundTracker()
        hook = create_save_hook(canvas, tracker, str(tmp_output_dir))
        msg = {"content": "text", "role": "assistant"}

        hook("painter", msg, "Critic", False)

        saved = tmp_output_dir / "round_01.png"
        with open(saved, "rb") as f:
            header = f.read(8)
        assert header[:4] == b"\x89PNG"

    # -- Guard: bare string message (AG2 send hooks receive str | dict) --

    def test_save_hook_string_message_saves_file(self, tmp_output_dir):
        canvas = Canvas()
        tracker = RoundTracker()
        hook = create_save_hook(canvas, tracker, str(tmp_output_dir))

        result = hook("painter", "done drawing", "Critic", False)

        assert (tmp_output_dir / "round_01.png").exists()
        assert tracker.current_round == 2
        assert result == "done drawing"

    # -- Guard: recipient is Agent instance with .name --

    def test_save_hook_agent_object_as_recipient_saves_file(self, tmp_output_dir):
        """Hook must handle real AG2 Agent instances (have .name) as recipient."""

        class _FakeAgent:
            def __init__(self, name):
                self.name = name

        canvas = Canvas()
        tracker = RoundTracker()
        hook = create_save_hook(canvas, tracker, str(tmp_output_dir))
        msg = {"content": "text", "role": "assistant"}

        hook("painter", msg, _FakeAgent("Critic"), False)

        assert (tmp_output_dir / "round_01.png").exists()


class TestStripAssistantImagesHookUnit:
    def test_strip_assistant_images_hook_returns_callable(self):
        hook = create_strip_assistant_images_hook()

        assert callable(hook)

    def test_strip_assistant_images_hook_removes_image_blocks_from_assistant_messages(
        self,
    ):
        canvas = Canvas()
        image = canvas.to_image_content()
        hook = create_strip_assistant_images_hook()
        messages = [
            {
                "role": "assistant",
                "content": [{"type": "text", "text": "reply"}, image],
            },
        ]

        result = hook(messages)

        types = [b["type"] for b in result[0]["content"]]
        assert "image_url" not in types
        assert "text" in types

    def test_strip_assistant_images_hook_leaves_user_messages_untouched(self):
        canvas = Canvas()
        image = canvas.to_image_content()
        hook = create_strip_assistant_images_hook()
        user_msg = {"role": "user", "content": [{"type": "text", "text": "hi"}, image]}

        result = hook([user_msg])

        assert result == [user_msg]

    def test_strip_assistant_images_hook_leaves_string_content_untouched(self):
        hook = create_strip_assistant_images_hook()
        msg = {"role": "assistant", "content": "plain text reply"}

        result = hook([msg])

        assert result == [msg]

    def test_strip_assistant_images_hook_does_not_mutate_input(self):
        canvas = Canvas()
        image = canvas.to_image_content()
        hook = create_strip_assistant_images_hook()
        messages = [
            {"role": "assistant", "content": [{"type": "text", "text": "r"}, image]},
        ]
        original = copy.deepcopy(messages)

        hook(messages)

        assert messages == original


class TestPruneStaleUserImagesHookUnit:
    def test_prune_stale_user_images_hook_returns_callable(self):
        hook = create_prune_stale_user_images_hook()

        assert callable(hook)

    def test_prune_stale_user_images_hook_keeps_image_on_only_last_user_message(self):
        canvas = Canvas()
        image = canvas.to_image_content()
        hook = create_prune_stale_user_images_hook()
        messages = [
            {"role": "user", "content": [{"type": "text", "text": "first"}, image]},
            {"role": "user", "content": [{"type": "text", "text": "last"}, image]},
        ]

        result = hook(messages)

        first_types = [b["type"] for b in result[0]["content"]]
        last_types = [b["type"] for b in result[-1]["content"]]
        assert "image_url" not in first_types
        assert "text" in first_types
        assert "image_url" in last_types

    def test_prune_stale_user_images_hook_leaves_assistant_messages_untouched(self):
        canvas = Canvas()
        image = canvas.to_image_content()
        hook = create_prune_stale_user_images_hook()
        assistant_msg = {
            "role": "assistant",
            "content": [{"type": "text", "text": "reply"}, image],
        }

        result = hook([assistant_msg])

        assert result == [assistant_msg]

    def test_prune_stale_user_images_hook_leaves_tool_messages_unchanged(self):
        hook = create_prune_stale_user_images_hook()
        tool_msg = {"role": "tool", "content": "draw result", "tool_call_id": "abc"}

        result = hook([tool_msg])

        assert result == [tool_msg]

    def test_prune_stale_user_images_hook_does_not_mutate_input(self):
        canvas = Canvas()
        image = canvas.to_image_content()
        hook = create_prune_stale_user_images_hook()
        messages = [
            {"role": "user", "content": [{"type": "text", "text": "a"}, image]},
            {"role": "user", "content": [{"type": "text", "text": "b"}, image]},
        ]
        original = copy.deepcopy(messages)

        hook(messages)

        assert messages == original
