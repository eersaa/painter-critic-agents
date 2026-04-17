import pytest
from autogen import ConversableAgent

from painter_critic.agents import create_agents
from painter_critic.config import DEFAULT_CRITIC_MODEL, DEFAULT_PAINTER_MODEL


class TestAgentsUnit:
    # --- Default models ---

    def test_agents_default_painter_model_matches_config_constant(self, api_url_env):
        painter, _, _ = create_agents("a tree")

        model = painter.llm_config["config_list"][0]["model"]
        assert model == DEFAULT_PAINTER_MODEL

    def test_agents_default_critic_model_matches_config_constant(self, api_url_env):
        _, _, critic = create_agents("a tree")

        model = critic.llm_config["config_list"][0]["model"]
        assert model == DEFAULT_CRITIC_MODEL

    # --- Agent names ---

    def test_agents_painter_name_is_painter(self, api_url_env):
        painter, _, _ = create_agents("a tree")

        assert painter.name == "Painter"

    def test_agents_critic_name_is_critic(self, api_url_env):
        _, _, critic = create_agents("a tree")

        assert critic.name == "Critic"

    # --- Critic system message mentions image/visual ---

    def test_agents_critic_system_message_mentions_image(self, api_url_env):
        _, _, critic = create_agents("a tree")

        msg = critic.system_message.lower()
        assert "image" in msg or "visual" in msg or "picture" in msg

    # --- Painter system message mentions tool names ---

    @pytest.mark.parametrize(
        "tool_name",
        ["draw_rectangle", "draw_circle", "draw_line", "draw_polygon"],
    )
    def test_agents_painter_system_message_mentions_tool(self, api_url_env, tool_name):
        painter, _, _ = create_agents("a tree")

        assert tool_name in painter.system_message

    # --- Special characters in subject ---

    def test_agents_special_characters_in_subject_no_crash(self, api_url_env):
        painter, painter_executor, critic = create_agents("a cat & dog")

        assert isinstance(painter, ConversableAgent)
        assert isinstance(painter_executor, ConversableAgent)
        assert isinstance(critic, ConversableAgent)

    def test_agents_special_characters_subject_appears_in_painter_message(
        self, api_url_env
    ):
        painter, _, _ = create_agents("a cat & dog")

        assert "a cat & dog" in painter.system_message

    # --- PainterExecutor.is_termination_msg ---

    def test_painter_executor_termination_callable_is_custom(self, api_url_env):
        """Default AG2 termination lambda always returns False for any dict;
        our custom one must return True for text-only replies."""
        _, painter_executor, _ = create_agents("a red circle")

        assert callable(painter_executor._is_termination_msg)
        assert painter_executor._is_termination_msg({"content": "anything"}) is True

    def test_painter_executor_terminates_on_tool_calls_none(self, api_url_env):
        _, painter_executor, _ = create_agents("a red circle")

        assert painter_executor._is_termination_msg(
            {"content": "done", "tool_calls": None}
        )

    def test_painter_executor_continues_on_single_tool_call(self, api_url_env):
        _, painter_executor, _ = create_agents("a red circle")

        assert not painter_executor._is_termination_msg(
            {"tool_calls": [{"id": "a", "function": {"name": "draw_circle"}}]}
        )

    def test_painter_executor_continues_on_multiple_tool_calls(self, api_url_env):
        _, painter_executor, _ = create_agents("a red circle")

        assert not painter_executor._is_termination_msg(
            {
                "tool_calls": [
                    {"id": "a", "function": {"name": "draw_circle"}},
                    {"id": "b", "function": {"name": "draw_rectangle"}},
                    {"id": "c", "function": {"name": "draw_line"}},
                ]
            }
        )

    # --- Painter system message: end-of-turn summary ---

    def test_painter_prompt_mentions_summary(self, api_url_env):
        painter, _, _ = create_agents("a red circle")

        assert "summar" in painter.system_message.lower()

    def test_painter_prompt_summary_colocated_with_handoff_language(self, api_url_env):
        """The summary instruction must be tied to turn/round end or handoff
        to Critic — not just the word "summary" in isolation."""
        painter, _, _ = create_agents("a red circle")

        msg = painter.system_message.lower()
        idx = msg.find("summar")
        assert idx != -1
        window = msg[max(0, idx - 120) : idx + 120]
        assert any(kw in window for kw in ("turn", "round", "critic", "hand")), (
            f"'summar' not near handoff language; window={window!r}"
        )

    def test_painter_prompt_old_forbidding_phrase_removed(self, api_url_env):
        """The old phrase actively forbids text replies; it must be gone so
        the new end-of-turn summary instruction is not contradicted."""
        painter, _, _ = create_agents("a red circle")

        forbidden = "your job is\n     to keep improving it every round"
        assert forbidden not in painter.system_message
