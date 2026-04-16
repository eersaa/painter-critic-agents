import os

import pytest
from autogen import ConversableAgent
from PIL import Image

from painter_critic.main import setup_pipeline


def _make_painter_mock(tools):
    """Mock reply: directly calls drawing tools, returns text summary."""
    call_count = [0]

    def reply(recipient, messages=None, sender=None, config=None):
        call_count[0] += 1
        if call_count[0] == 1:
            tools["draw_rectangle"](10, 10, 80, 80, "#FF0000")
            return (True, "Drew a red rectangle")
        elif call_count[0] == 2:
            tools["draw_circle"](150, 50, 30, "#FFFF00")
            return (True, "Added a yellow circle")
        else:
            tools["draw_line"](0, 150, 199, 150, "#00FF00", 3)
            return (True, "Added a green line")

    return reply


def _critic_mock(recipient, messages=None, sender=None, config=None):
    """Mock reply: returns static feedback text."""
    return (True, "CRITIC_FEEDBACK: Add more details to improve the picture.")


def _run_mocked_pipeline(output_dir, rounds=3, painter_reply_factory=None):
    """Use real setup_pipeline wiring, inject mock LLM replies, run chat.

    Args:
        output_dir: Directory for output images.
        rounds: Number of conversation rounds.
        painter_reply_factory: Callable(tools) -> reply_func. If None, uses default mock.

    Returns (ChatResult, canvas, tools).
    """
    painter, critic, canvas, tools = setup_pipeline("test subject", output_dir)

    if painter_reply_factory:
        reply_func = painter_reply_factory(tools)
    else:
        reply_func = _make_painter_mock(tools)

    painter.register_reply(
        trigger=ConversableAgent,
        reply_func=reply_func,
        remove_other_reply_funcs=True,
    )
    critic.register_reply(
        trigger=ConversableAgent,
        reply_func=_critic_mock,
        remove_other_reply_funcs=True,
    )

    result = critic.initiate_chat(
        painter, message="Please draw: test subject", max_turns=rounds, silent=True
    )
    return result, canvas, tools


class TestPipelineAcceptance:
    def test_pipeline_n_rounds_produces_n_images(self, tmp_output_dir, api_url_env):
        rounds = 3
        _run_mocked_pipeline(str(tmp_output_dir), rounds=rounds)

        for i in range(1, rounds + 1):
            assert os.path.exists(tmp_output_dir / f"round_{i:02d}.png")

    def test_pipeline_output_images_are_200x200(self, tmp_output_dir, api_url_env):
        _run_mocked_pipeline(str(tmp_output_dir), rounds=1)

        img = Image.open(tmp_output_dir / "round_01.png")
        assert img.size == (200, 200)

    def test_pipeline_consecutive_images_differ(self, tmp_output_dir, api_url_env):
        _run_mocked_pipeline(str(tmp_output_dir), rounds=2)

        bytes_1 = (tmp_output_dir / "round_01.png").read_bytes()
        bytes_2 = (tmp_output_dir / "round_02.png").read_bytes()
        assert bytes_1 != bytes_2

    def test_pipeline_later_round_preserves_earlier_drawing(
        self, tmp_output_dir, api_url_env
    ):
        _run_mocked_pipeline(str(tmp_output_dir), rounds=2)

        img = Image.open(tmp_output_dir / "round_02.png")
        # Round 1 mock draws red rectangle at (10,10)-(80,80); pixel (50,50) should be red
        pixel = img.getpixel((50, 50))
        assert pixel[0] > 200, f"Red channel {pixel[0]} too low — round 1 drawing lost"

    def test_pipeline_conversation_log_contains_agent_names(
        self, tmp_output_dir, api_url_env
    ):
        from painter_critic.main import save_conversation_log

        result, _, _ = _run_mocked_pipeline(str(tmp_output_dir), rounds=2)
        save_conversation_log(result.chat_history, str(tmp_output_dir))

        log_path = tmp_output_dir / "conversation.log"
        assert log_path.exists()
        content = log_path.read_text()
        assert "Painter" in content
        assert "Critic" in content

    def test_pipeline_conversation_log_excludes_base64_images(
        self, tmp_output_dir, api_url_env
    ):
        from painter_critic.main import save_conversation_log

        result, _, _ = _run_mocked_pipeline(str(tmp_output_dir), rounds=2)
        save_conversation_log(result.chat_history, str(tmp_output_dir))

        content = (tmp_output_dir / "conversation.log").read_text()
        assert "data:image/png;base64," not in content

    def test_pipeline_critic_messages_contain_image_url_block(
        self, tmp_output_dir, api_url_env
    ):
        result, _, _ = _run_mocked_pipeline(str(tmp_output_dir), rounds=2)

        critic_messages = [m for m in result.chat_history if m.get("name") == "Critic"]
        assert len(critic_messages) > 0
        has_image = any(
            isinstance(m.get("content"), list)
            and any(b.get("type") == "image_url" for b in m["content"])
            for m in critic_messages
        )
        assert has_image

    def test_pipeline_painter_receives_messages_with_image_url_block(
        self, tmp_output_dir, api_url_env
    ):
        captured = []

        def capturing_factory(tools):
            def reply(recipient, messages=None, sender=None, config=None):
                captured.append(messages)
                tools["draw_rectangle"](10, 10, 80, 80, "#FF0000")
                return (True, "Drew something")

            return reply

        _run_mocked_pipeline(
            str(tmp_output_dir), rounds=2, painter_reply_factory=capturing_factory
        )

        assert len(captured) > 0
        has_image = any(
            isinstance(msg.get("content"), list)
            and any(b.get("type") == "image_url" for b in msg["content"])
            for msg_list in captured
            for msg in msg_list
        )
        assert has_image

    def test_pipeline_critic_feedback_text_reaches_painter(
        self, tmp_output_dir, api_url_env
    ):
        captured = []

        def capturing_factory(tools):
            def reply(recipient, messages=None, sender=None, config=None):
                captured.append(messages)
                tools["draw_rectangle"](10, 10, 80, 80, "#FF0000")
                return (True, "Drew something")

            return reply

        _run_mocked_pipeline(
            str(tmp_output_dir), rounds=3, painter_reply_factory=capturing_factory
        )

        # Round 2+ messages should contain Critic's feedback text
        assert len(captured) >= 2
        all_text = ""
        for msg in captured[1]:
            content = msg.get("content", "")
            if isinstance(content, str):
                all_text += content
            elif isinstance(content, list):
                for block in content:
                    if block.get("type") == "text":
                        all_text += block.get("text", "")
        assert "CRITIC_FEEDBACK" in all_text


@pytest.mark.slow
class TestPipelineSlowAcceptance:
    @pytest.fixture(scope="class")
    def real_pipeline_output(self, tmp_path_factory):
        from dotenv import load_dotenv

        load_dotenv()

        from painter_critic.main import run_pipeline

        output_dir = tmp_path_factory.mktemp("slow_output")
        run_pipeline(
            prompt="a red circle on blue background",
            rounds=2,
            output_dir=str(output_dir),
        )
        return output_dir

    def test_pipeline_real_api_two_rounds_produces_images(self, real_pipeline_output):
        assert os.path.exists(real_pipeline_output / "round_01.png")
        assert os.path.exists(real_pipeline_output / "round_02.png")

    def test_pipeline_real_api_output_images_are_200x200(self, real_pipeline_output):
        img = Image.open(real_pipeline_output / "round_01.png")
        assert img.size == (200, 200)
