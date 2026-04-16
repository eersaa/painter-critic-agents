from painter_critic.canvas import Canvas
from painter_critic.hooks import RoundTracker, create_reply_hook, create_send_hook


class TestHooksAcceptance:
    def test_hooks_round_tracker_initial_round_returns_round_01_path(self):
        tracker = RoundTracker()

        assert tracker.get_image_path("output") == "output/round_01.png"

    def test_hooks_round_tracker_after_increments_returns_correct_path(self):
        tracker = RoundTracker()
        for _ in range(4):
            tracker.increment()

        assert tracker.get_image_path("output") == "output/round_05.png"

    def test_hooks_send_hook_attaches_image_to_text_message(self):
        canvas = Canvas()
        hook = create_send_hook(canvas)

        message = {"content": "Here is my feedback", "role": "user"}
        # AG2 process_message_before_send signature: (sender, message, recipient, silent)
        result = hook(None, message, None, False)

        assert isinstance(result["content"], list)
        types = [block["type"] for block in result["content"]]
        assert "text" in types
        assert "image_url" in types

    def test_hooks_reply_hook_injects_image_into_last_message(self):
        canvas = Canvas()
        hook = create_reply_hook(canvas)

        messages = [
            {"content": "first message", "role": "user"},
            {"content": "second message", "role": "assistant"},
        ]
        result = hook(messages)

        assert len(result) == len(messages)
        assert result[0]["content"] == "first message"
        last_types = [block["type"] for block in result[-1]["content"]]
        assert "text" in last_types
        assert "image_url" in last_types
