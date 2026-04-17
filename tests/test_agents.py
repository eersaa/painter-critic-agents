from autogen import ConversableAgent

from painter_critic.agents import create_agents
from painter_critic.config import CANVAS_SIZE


class TestAgentsAcceptance:
    def test_create_agents_returns_three_conversable_agents(self, api_url_env):
        painter, painter_executor, critic = create_agents("a red circle")

        assert isinstance(painter, ConversableAgent)
        assert isinstance(painter_executor, ConversableAgent)
        assert isinstance(critic, ConversableAgent)

    def test_create_agents_three_distinct_names(self, api_url_env):
        painter, painter_executor, critic = create_agents("a red circle")

        assert len({painter.name, painter_executor.name, critic.name}) == 3

    def test_agents_have_distinct_system_messages(self, api_url_env):
        painter, _, critic = create_agents("a red circle")

        assert painter.system_message
        assert critic.system_message
        assert painter.system_message != critic.system_message

    def test_painter_system_message_contains_subject(self, api_url_env):
        painter, _, _ = create_agents("a house with a sun")

        assert "a house with a sun" in painter.system_message

    def test_painter_system_message_contains_coordinate_bounds(self, api_url_env):
        painter, _, _ = create_agents("a red circle")

        assert str(CANVAS_SIZE - 1) in painter.system_message

    def test_critic_system_message_contains_feedback_instructions(self, api_url_env):
        _, _, critic = create_agents("a red circle")

        msg = critic.system_message.lower()
        assert "feedback" in msg or "improve" in msg or "suggest" in msg

    def test_agents_human_input_mode_is_never(self, api_url_env):
        painter, painter_executor, critic = create_agents("a red circle")

        assert painter.human_input_mode == "NEVER"
        assert painter_executor.human_input_mode == "NEVER"
        assert critic.human_input_mode == "NEVER"

    def test_create_agents_uses_specified_painter_model(self, api_url_env):
        painter, _, _ = create_agents("a circle", painter_model="custom/painter")

        assert painter.llm_config["config_list"][0]["model"] == "custom/painter"

    def test_create_agents_uses_specified_critic_model(self, api_url_env):
        _, _, critic = create_agents("a circle", critic_model="custom/critic")

        assert critic.llm_config["config_list"][0]["model"] == "custom/critic"

    def test_painter_system_message_contains_image_instruction(self, api_url_env):
        painter, _, _ = create_agents("a red circle")

        assert "canvas image" in painter.system_message

    def test_critic_system_message_contains_subject(self, api_url_env):
        _, _, critic = create_agents("a blue triangle")

        assert "a blue triangle" in critic.system_message

    def test_painter_executor_has_no_llm(self, api_url_env):
        _, painter_executor, _ = create_agents("a red circle")

        assert not painter_executor.llm_config

    def test_painter_executor_terminates_on_text_only_reply(self, api_url_env):
        _, painter_executor, _ = create_agents("a red circle")

        assert painter_executor._is_termination_msg(
            {"content": "round done, over to critic", "role": "assistant"}
        )

    def test_painter_executor_continues_on_tool_call_reply(self, api_url_env):
        _, painter_executor, _ = create_agents("a red circle")

        assert not painter_executor._is_termination_msg(
            {
                "tool_calls": [{"id": "x", "function": {"name": "draw_rectangle"}}],
                "role": "assistant",
            }
        )

    def test_painter_executor_terminates_on_empty_tool_calls_list(self, api_url_env):
        """Edge case: empty list is falsy — our check treats missing-or-empty
        tool_calls as text-only and terminates. AG2 never sends tool_calls=[]
        in practice, but the contract should be explicit."""
        _, painter_executor, _ = create_agents("a red circle")

        assert painter_executor._is_termination_msg(
            {"tool_calls": [], "content": "text", "role": "assistant"}
        )

    def test_painter_system_message_instructs_end_of_turn_summary(self, api_url_env):
        """Painter must emit a short text summary after drawing to hand off to
        Critic. This signal triggers PainterExecutor.is_termination_msg."""
        painter, _, _ = create_agents("a red circle")

        assert "summar" in painter.system_message.lower()
