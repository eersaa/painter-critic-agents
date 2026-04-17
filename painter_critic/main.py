from pathlib import Path

from dotenv import load_dotenv

from painter_critic.agents import create_agents
from painter_critic.canvas import Canvas
from painter_critic.config import (
    CANVAS_SIZE,
    DEFAULT_CRITIC_MODEL,
    DEFAULT_PAINTER_MODEL,
    DEFAULT_ROUNDS,
    MAX_TOOL_ITERATIONS,
    OUTPUT_DIR,
    parse_args,
)
from painter_critic.hooks import (
    RoundTracker,
    create_reply_hook,
    create_save_hook,
    create_send_hook,
    create_strip_images_hook,
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
    rounds=DEFAULT_ROUNDS,
    output_dir=OUTPUT_DIR,
    painter_model=DEFAULT_PAINTER_MODEL,
    critic_model=DEFAULT_CRITIC_MODEL,
):
    """Create and wire all components. Returns (painter, painter_executor, critic, canvas, tools, tracker)."""
    canvas = Canvas(CANVAS_SIZE, CANVAS_SIZE)
    tools = create_tools(canvas)
    painter, painter_executor, critic = create_agents(
        prompt, painter_model, critic_model, CANVAS_SIZE
    )

    # Painter LLM generates tool calls; PainterExecutor executes them
    for func in tools.values():
        painter.register_for_llm(description=func.__doc__)(func)
        painter_executor.register_for_execution()(func)

    painter.register_nested_chats(
        trigger=critic,
        chat_queue=[
            {
                "sender": painter_executor,
                "recipient": painter,
                "max_turns": MAX_TOOL_ITERATIONS,
                "summary_method": "last_msg",
            }
        ],
    )

    tracker = RoundTracker()
    critic.register_hook("process_message_before_send", create_send_hook(canvas))
    # Strip images from assistant messages before Critic's LLM (some models reject them)
    critic.register_hook(
        "process_all_messages_before_reply", create_strip_images_hook()
    )
    critic.register_hook("process_all_messages_before_reply", create_reply_hook(canvas))
    painter.register_hook(
        "process_message_before_send", create_save_hook(canvas, tracker, output_dir)
    )

    return painter, painter_executor, critic, canvas, tools, tracker


def run_pipeline(
    prompt,
    rounds=DEFAULT_ROUNDS,
    output_dir=OUTPUT_DIR,
    painter_model=DEFAULT_PAINTER_MODEL,
    critic_model=DEFAULT_CRITIC_MODEL,
):
    painter, painter_executor, critic, canvas, tools, tracker = setup_pipeline(
        prompt, rounds, output_dir, painter_model, critic_model
    )

    # Phase 1: pre-draw. Executor kicks off Painter's LLM↔tool loop to produce first attempt.
    painter_executor.initiate_chat(
        painter,
        message={
            "content": [
                {"type": "text", "text": f"Paint: {prompt}"},
                canvas.to_image_content(),
            ]
        },
        max_turns=MAX_TOOL_ITERATIONS,
        clear_history=True,
    )

    # Phase 2: critique loop. Painter initiates with Critic.
    # max_turns = rounds * 2 → `rounds` painter sends + `rounds` critic replies.
    result = painter.initiate_chat(
        critic,
        message=f"I have painted: {prompt}. Please review.",
        max_turns=rounds * 2,
    )
    return result


def main(argv: list[str] | None = None) -> None:
    load_dotenv()
    args = parse_args(argv)
    result = run_pipeline(
        args.prompt, args.rounds, OUTPUT_DIR, args.painter_model, args.critic_model
    )
    save_conversation_log(result.chat_history, OUTPUT_DIR)
