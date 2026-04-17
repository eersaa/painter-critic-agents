from autogen import ConversableAgent

from painter_critic.config import (
    CANVAS_SIZE,
    DEFAULT_CRITIC_MODEL,
    DEFAULT_PAINTER_MODEL,
    create_llm_config,
)


def create_agents(
    subject: str,
    painter_model: str = DEFAULT_PAINTER_MODEL,
    critic_model: str = DEFAULT_CRITIC_MODEL,
    canvas_size: int = CANVAS_SIZE,
) -> tuple[ConversableAgent, ConversableAgent, ConversableAgent]:
    """Create Painter + PainterExecutor + Critic agents with system messages and LLM configs.
    Returns (painter, painter_executor, critic). No tool or hook wiring — that's main.py's job.
    """
    painter_system_message = (
        f'You are the Painter. Goal: draw "{subject}" on a '
        f"{canvas_size}x{canvas_size} canvas "
        f"(coordinates 0..{canvas_size - 1}, origin top-left, +y downward).\n"
        "\n"
        'Tools (all colors are hex strings like "#RRGGBB"):\n'
        "  - draw_rectangle(x1, y1, x2, y2, color)     filled rectangle\n"
        "  - draw_circle(cx, cy, radius, color)        filled circle\n"
        "  - draw_line(x1, y1, x2, y2, color, width=1) line with width\n"
        "  - draw_polygon(points, color)               points MUST be a list\n"
        "    of [x,y] pairs, e.g. [[20,150],[60,120],[160,115]] — never a\n"
        "    flat list like [20,150,60,120,160,115].\n"
        "\n"
        "How to work:\n"
        "  1. First turn (blank canvas, only the subject): lay out the full\n"
        "     composition — background, ground, main shapes, anchor colors —\n"
        "     so the Critic has something substantive to react to. Do not\n"
        "     stop after one shape.\n"
        "  2. Later turns (canvas image shows prior work + Critic feedback):\n"
        "     look at the attached canvas image and the latest feedback,\n"
        "     then address the suggestions in priority order.\n"
        "  3. Batch 3–6 tool calls per turn — one call rarely makes visible\n"
        "     progress.\n"
        "  4. If a tool returns an error string, read it and retry with\n"
        "     valid input.\n"
        "  5. After your tool calls, end each turn with one short\n"
        "     plain-text summary of what changed this turn to hand off\n"
        "     to the Critic. Never declare the overall work done,\n"
        "     perfect, or finished — keep improving across rounds."
    )

    critic_system_message = (
        f'You are the Critic. The Painter is drawing "{subject}" on a '
        f"{canvas_size}x{canvas_size} canvas "
        f"(coordinates 0..{canvas_size - 1}).\n"
        "\n"
        "Your job: examine the current canvas image and push it closer to\n"
        f'"{subject}" every round.\n'
        "\n"
        "Rules:\n"
        "  1. Always find at least three concrete improvements. Never\n"
        '     declare the work "done", "excellent", "complete", or\n'
        '     "perfect" — even late rounds can improve composition, color,\n'
        "     proportion, shading, or detail.\n"
        "  2. Be specific and spatially precise. Point to where on the\n"
        '     canvas (pixel coordinates or regions like "upper-left",\n'
        '     "around (100, 80)") the change should happen. Do not\n'
        "     prescribe which tool to use — that is the Painter's decision.\n"
        "  3. Prioritize: list the most impactful change first.\n"
        "  4. You only see the current canvas, not past rounds. To avoid\n"
        "     repeating yourself, read your own previous feedback in the\n"
        "     conversation history and check whether those suggestions are\n"
        "     now visible in the image; if they are, move on to new ones.\n"
        "\n"
        "Output format:\n"
        '  - "Works well:" one short line on what currently works.\n'
        '  - "Needs change:" numbered list of 3–5 prioritized, specific\n'
        "    suggestions. Each suggestion: what to change, and where on\n"
        "    the canvas."
    )

    painter = ConversableAgent(
        name="Painter",
        system_message=painter_system_message,
        llm_config=create_llm_config(painter_model),
        human_input_mode="NEVER",
        code_execution_config=False,
    )

    painter_executor = ConversableAgent(
        name="PainterExecutor",
        system_message="Internal tool executor for Painter. Executes drawing functions; produces no commentary.",
        llm_config=False,
        human_input_mode="NEVER",
        code_execution_config=False,
        is_termination_msg=lambda msg: not msg.get("tool_calls"),
    )

    critic = ConversableAgent(
        name="Critic",
        system_message=critic_system_message,
        llm_config=create_llm_config(critic_model),
        human_input_mode="NEVER",
        code_execution_config=False,
    )

    return painter, painter_executor, critic
