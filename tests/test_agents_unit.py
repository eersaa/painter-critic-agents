from autogen import ConversableAgent

from painter_critic.agents import create_agents
from painter_critic.config import DEFAULT_CRITIC_MODEL, DEFAULT_PAINTER_MODEL


class TestAgentsUnit:
    # --- Default models ---

    def test_agents_default_painter_model_matches_config_constant(self, api_url_env):
        painter, _ = create_agents("a tree")

        model = painter.llm_config["config_list"][0]["model"]
        assert model == DEFAULT_PAINTER_MODEL

    def test_agents_default_critic_model_matches_config_constant(self, api_url_env):
        _, critic = create_agents("a tree")

        model = critic.llm_config["config_list"][0]["model"]
        assert model == DEFAULT_CRITIC_MODEL

    # --- Agent names ---

    def test_agents_painter_name_is_painter(self, api_url_env):
        painter, _ = create_agents("a tree")

        assert painter.name == "Painter"

    def test_agents_critic_name_is_critic(self, api_url_env):
        _, critic = create_agents("a tree")

        assert critic.name == "Critic"

    # --- Critic system message mentions image/visual ---

    def test_agents_critic_system_message_mentions_image(self, api_url_env):
        _, critic = create_agents("a tree")

        msg = critic.system_message.lower()
        assert "image" in msg or "visual" in msg or "picture" in msg

    # --- Painter system message mentions tool names ---

    def test_agents_painter_system_message_mentions_draw_rectangle(self, api_url_env):
        painter, _ = create_agents("a tree")

        assert "draw_rectangle" in painter.system_message

    def test_agents_painter_system_message_mentions_draw_circle(self, api_url_env):
        painter, _ = create_agents("a tree")

        assert "draw_circle" in painter.system_message

    def test_agents_painter_system_message_mentions_draw_line(self, api_url_env):
        painter, _ = create_agents("a tree")

        assert "draw_line" in painter.system_message

    def test_agents_painter_system_message_mentions_draw_polygon(self, api_url_env):
        painter, _ = create_agents("a tree")

        assert "draw_polygon" in painter.system_message

    # --- Special characters in subject ---

    def test_agents_special_characters_in_subject_no_crash(self, api_url_env):
        painter, critic = create_agents("a cat & dog")

        assert isinstance(painter, ConversableAgent)
        assert isinstance(critic, ConversableAgent)

    def test_agents_special_characters_subject_appears_in_painter_message(
        self, api_url_env
    ):
        painter, _ = create_agents("a cat & dog")

        assert "a cat & dog" in painter.system_message

    # --- B2: Painter image awareness ---

    def test_agents_painter_message_mentions_canvas_image(self, api_url_env):
        painter, _ = create_agents("a tree")

        assert "canvas image" in painter.system_message

    # --- B3: Subject in Critic message ---

    def test_agents_critic_message_contains_subject(self, api_url_env):
        _, critic = create_agents("a blue triangle")

        assert "a blue triangle" in critic.system_message
