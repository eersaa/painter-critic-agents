from autogen import ConversableAgent

from painter_critic.agents import create_agents
from painter_critic.config import CANVAS_SIZE


class TestAgentsAcceptance:
    def test_create_agents_returns_two_conversable_agents(self, api_url_env):
        painter, critic = create_agents("a red circle")

        assert isinstance(painter, ConversableAgent)
        assert isinstance(critic, ConversableAgent)

    def test_create_agents_painter_and_critic_have_distinct_names(self, api_url_env):
        painter, critic = create_agents("a red circle")

        assert painter.name != critic.name

    def test_agents_have_distinct_system_messages(self, api_url_env):
        painter, critic = create_agents("a red circle")

        assert painter.system_message
        assert critic.system_message
        assert painter.system_message != critic.system_message

    def test_painter_system_message_contains_subject(self, api_url_env):
        painter, _ = create_agents("a house with a sun")

        assert "a house with a sun" in painter.system_message

    def test_painter_system_message_contains_coordinate_bounds(self, api_url_env):
        painter, _ = create_agents("a red circle")

        # Painter must know the canvas coordinate range (0,0)-(max,max)
        assert str(CANVAS_SIZE - 1) in painter.system_message

    def test_critic_system_message_contains_feedback_instructions(self, api_url_env):
        _, critic = create_agents("a red circle")

        msg = critic.system_message.lower()
        assert "feedback" in msg or "improve" in msg or "suggest" in msg

    def test_agents_human_input_mode_is_never(self, api_url_env):
        painter, critic = create_agents("a red circle")

        assert painter.human_input_mode == "NEVER"
        assert critic.human_input_mode == "NEVER"

    def test_create_agents_uses_specified_painter_model(self, api_url_env):
        painter, _ = create_agents("a circle", painter_model="custom/painter")

        assert painter.llm_config["config_list"][0]["model"] == "custom/painter"

    def test_create_agents_uses_specified_critic_model(self, api_url_env):
        _, critic = create_agents("a circle", critic_model="custom/critic")

        assert critic.llm_config["config_list"][0]["model"] == "custom/critic"

    def test_painter_system_message_contains_image_instruction(self, api_url_env):
        painter, _ = create_agents("a red circle")

        assert "canvas image" in painter.system_message

    def test_critic_system_message_contains_subject(self, api_url_env):
        _, critic = create_agents("a blue triangle")

        assert "a blue triangle" in critic.system_message
