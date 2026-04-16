from pathlib import Path

from dotenv import load_dotenv

from painter_critic.agents import create_agents
from painter_critic.canvas import Canvas
from painter_critic.config import (
    CANVAS_SIZE,
    DEFAULT_CRITIC_MODEL,
    DEFAULT_PAINTER_MODEL,
    DEFAULT_ROUNDS,
    OUTPUT_DIR,
    parse_args,
)
from painter_critic.hooks import (
    RoundTracker,
    create_reply_hook,
    create_save_hook,
    create_send_hook,
)
from painter_critic.tools import create_tools


def save_conversation_log(chat_history: list[dict], output_dir: str) -> None:
    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)
    log_path = out / "conversation.log"

    lines = []
    for msg in chat_history:
        name = msg.get("name", "Unknown")
        content = msg.get("content")

        if content is None:
            text = "[tool call]"
        elif isinstance(content, list):
            text_blocks = [
                block["text"] for block in content if block.get("type") == "text"
            ]
            text = "\n".join(text_blocks)
        else:
            text = content

        lines.append(f"--- {name} ---\n{text}\n\n")

    log_path.write_text("".join(lines))


def setup_pipeline(
    prompt,
    output_dir=OUTPUT_DIR,
    painter_model=DEFAULT_PAINTER_MODEL,
    critic_model=DEFAULT_CRITIC_MODEL,
):
    """Create and wire all components. Returns (painter, critic, canvas, tools)."""
    canvas = Canvas(CANVAS_SIZE, CANVAS_SIZE)
    tools = create_tools(canvas)
    painter, critic = create_agents(prompt, painter_model, critic_model, CANVAS_SIZE)

    for func in tools.values():
        painter.register_for_llm(description=func.__doc__)(func)
        painter.register_for_execution()(func)

    tracker = RoundTracker()
    critic.register_hook("process_message_before_send", create_send_hook(canvas))
    critic.register_hook("process_all_messages_before_reply", create_reply_hook(canvas))
    painter.register_hook(
        "process_message_before_send", create_save_hook(canvas, tracker, output_dir)
    )

    return painter, critic, canvas, tools


def run_pipeline(
    prompt,
    rounds=DEFAULT_ROUNDS,
    output_dir=OUTPUT_DIR,
    painter_model=DEFAULT_PAINTER_MODEL,
    critic_model=DEFAULT_CRITIC_MODEL,
):
    painter, critic, canvas, tools = setup_pipeline(
        prompt, output_dir, painter_model, critic_model
    )
    result = critic.initiate_chat(
        painter, message=f"Please draw: {prompt}", max_turns=rounds
    )
    return result


def main(argv: list[str] | None = None) -> None:
    load_dotenv()
    args = parse_args(argv)
    result = run_pipeline(
        args.prompt, args.rounds, OUTPUT_DIR, args.painter_model, args.critic_model
    )
    save_conversation_log(result.chat_history, OUTPUT_DIR)
