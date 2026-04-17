from collections.abc import Callable

from painter_critic.canvas import Canvas


class RoundTracker:
    def __init__(self):
        self._round = 1

    @property
    def current_round(self) -> int:
        return self._round

    def increment(self) -> None:
        self._round += 1

    def get_image_path(self, output_dir: str) -> str:
        return f"{output_dir}/round_{self._round:02d}.png"


def _is_tool_message(message: dict | str) -> bool:
    if isinstance(message, str):
        return False
    return "tool_calls" in message or message.get("role") == "tool"


def _append_image(content, image_block: dict) -> list:
    if isinstance(content, list):
        return list(content) + [image_block]
    return [{"type": "text", "text": content}, image_block]


def create_send_hook(canvas: Canvas) -> Callable:
    def hook(sender, message, recipient, silent):
        if isinstance(message, str):
            return {
                "content": [
                    {"type": "text", "text": message},
                    canvas.to_image_content(),
                ]
            }

        if isinstance(message, dict):
            if _is_tool_message(message):
                return message
            result = dict(message)
            result["content"] = _append_image(
                result["content"], canvas.to_image_content()
            )
            return result

        return message

    return hook


def create_save_hook(
    canvas: Canvas, tracker: RoundTracker, output_dir: str
) -> Callable:
    def hook(sender, message, recipient, silent):
        recipient_name = getattr(recipient, "name", recipient)
        if recipient_name != "Critic":
            return message
        if _is_tool_message(message):
            return message
        canvas.save(tracker.get_image_path(output_dir))
        tracker.increment()
        return message

    return hook


def _strip_images(msg: dict) -> dict:
    """Return a copy of msg with image_url blocks removed from its content."""
    stripped = dict(msg)
    content = msg.get("content")
    if isinstance(content, list):
        stripped["content"] = [b for b in content if b.get("type") != "image_url"]
    return stripped


def create_strip_assistant_images_hook() -> Callable:
    """Strip image_url blocks from every assistant message.

    Reason: API compliance — OpenAI/Anthropic chat APIs reject images in assistant turns.
    """

    def hook(messages: list[dict]) -> list[dict]:
        return [
            _strip_images(msg)
            if msg.get("role") == "assistant" and isinstance(msg.get("content"), list)
            else msg
            for msg in messages
        ]

    return hook


def create_prune_stale_user_images_hook() -> Callable:
    """Strip image_url blocks from every user message except the last one.

    Reason: preventing stale canvas accumulation across rounds — reply_hook
    re-attaches the current canvas to the last message.
    """

    def hook(messages: list[dict]) -> list[dict]:
        last_user_idx = next(
            (
                i
                for i in range(len(messages) - 1, -1, -1)
                if messages[i].get("role") == "user"
            ),
            None,
        )

        return [
            msg
            if not (
                msg.get("role") == "user"
                and isinstance(msg.get("content"), list)
                and i != last_user_idx
            )
            else _strip_images(msg)
            for i, msg in enumerate(messages)
        ]

    return hook


def create_reply_hook(canvas: Canvas) -> Callable:
    def hook(messages: list[dict]) -> list[dict]:
        if not messages:
            return messages

        target_idx = next(
            (
                i
                for i in range(len(messages) - 1, -1, -1)
                if not _is_tool_message(messages[i])
            ),
            None,
        )

        if target_idx is None:
            return messages

        target = messages[target_idx]
        new_msg = _strip_images(target)
        new_msg["content"] = _append_image(
            new_msg["content"], canvas.to_image_content()
        )

        return (
            list(messages[:target_idx]) + [new_msg] + list(messages[target_idx + 1 :])
        )

    return hook
