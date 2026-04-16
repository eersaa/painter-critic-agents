from autogen import ConversableAgent

from painter_critic.config import (
    DEFAULT_CRITIC_MODEL,
    DEFAULT_PAINTER_MODEL,
    create_llm_config,
)


def create_agents(
    subject: str,
    painter_model: str = DEFAULT_PAINTER_MODEL,
    critic_model: str = DEFAULT_CRITIC_MODEL,
) -> tuple[ConversableAgent, ConversableAgent]:
    """Create Painter + Critic agents with system messages and LLM configs.
    Returns (painter, critic). No tool or hook wiring — that's main.py's job.
    """
    painter_system_message = (
        f"You are a Painter agent. Your task is to draw: {subject}.\n"
        "Use the available drawing tools to create the image on a 200x200 canvas. "
        "Coordinates range from 0 to 199 on both axes.\n"
        "Available tools: draw_rectangle, draw_circle, draw_line, draw_polygon.\n"
        "Call these tools to incrementally build up the image."
    )

    critic_system_message = (
        "You are a Critic agent. Your task is to review the current image "
        "and provide constructive feedback to help improve the visual result. "
        "Suggest specific changes the Painter can make to better achieve the desired picture."
    )

    painter = ConversableAgent(
        name="Painter",
        system_message=painter_system_message,
        llm_config=create_llm_config(painter_model),
        human_input_mode="NEVER",
        code_execution_config=False,
    )

    critic = ConversableAgent(
        name="Critic",
        system_message=critic_system_message,
        llm_config=create_llm_config(critic_model),
        human_input_mode="NEVER",
        code_execution_config=False,
    )

    return painter, critic
