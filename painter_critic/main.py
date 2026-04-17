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
    create_prune_stale_user_images_hook,
    create_reply_hook,
    create_save_hook,
    create_send_hook,
    create_strip_assistant_images_hook,
)
from painter_critic.tools import create_tools


def save_conversation_log(
    chat_history: list[dict], output_dir: str, prompt: str
) -> None:
    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)
    log_path = out / "conversation.log"

    lines = [f"--- User ---\nPaint: {prompt}\n\n"]
    for msg in chat_history:
        name = msg.get("name", "Unknown")
        content = msg.get("content")

        if content is None:
            text = "[tool call]"
        elif isinstance(content, list):
            text = "\n".join(
                block["text"] for block in content if block.get("type") == "text"
            )
        else:
            text = content

        lines.append(f"--- {name} ---\n{text}\n\n")

    log_path.write_text("".join(lines))


def _nested_chat_message(recipient, messages, sender, config):
    # AG2 passes messages[-1]["content"] directly as the nested chat's initial
    # message. When Critic's send_hook produced multimodal list content, that
    # bare list trips _append_oai_message validation. Wrap it in a dict.
    content = messages[-1].get("content", "")
    if isinstance(content, list):
        return {"content": content}
    return content or ""


def _phase1_message(prompt, canvas):
    return {
        "content": [
            {"type": "text", "text": f"Paint: {prompt}"},
            canvas.to_image_content(),
        ]
    }


def setup_pipeline(
    prompt,
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
                "message": _nested_chat_message,
                "max_turns": MAX_TOOL_ITERATIONS,
                "summary_method": "last_msg",
            }
        ],
    )

    tracker = RoundTracker()
    critic.register_hook("process_message_before_send", create_send_hook(canvas))
    # Strip assistant images (API compliance) + prune stale user images + inject current canvas
    critic.register_hook(
        "process_all_messages_before_reply", create_strip_assistant_images_hook()
    )
    critic.register_hook(
        "process_all_messages_before_reply", create_prune_stale_user_images_hook()
    )
    critic.register_hook("process_all_messages_before_reply", create_reply_hook(canvas))
    painter.register_hook(
        "process_all_messages_before_reply", create_strip_assistant_images_hook()
    )
    painter.register_hook(
        "process_all_messages_before_reply", create_prune_stale_user_images_hook()
    )
    painter.register_hook(
        "process_all_messages_before_reply", create_reply_hook(canvas)
    )
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
        prompt, output_dir, painter_model, critic_model
    )

    # Phase 1: pre-draw. Executor kicks off Painter's LLM↔tool loop to produce first attempt.
    painter_executor.initiate_chat(
        painter,
        message=_phase1_message(prompt, canvas),
        max_turns=MAX_TOOL_ITERATIONS,
        clear_history=True,
    )

    # Phase 2: critique loop. Painter initiates with Critic.
    # max_turns = number of rounds to iterate on the drawing
    result = painter.initiate_chat(
        critic,
        message="Please critique the canvas.",
        max_turns=rounds,
    )
    return result


def main(argv: list[str] | None = None) -> None:
    load_dotenv()
    args = parse_args(argv)
    result = run_pipeline(
        args.prompt, args.rounds, OUTPUT_DIR, args.painter_model, args.critic_model
    )
    save_conversation_log(result.chat_history, OUTPUT_DIR, args.prompt)
