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


def create_strip_images_hook() -> Callable:
    """Strip image_url blocks from assistant messages before LLM call.

    Some models reject images in assistant-role messages. This hook removes
    them so only user-role messages contain images.
    """

    def hook(messages: list[dict]) -> list[dict]:
        result = []
        for msg in messages:
            if msg.get("role") == "assistant" and isinstance(msg.get("content"), list):
                msg_copy = dict(msg)
                msg_copy["content"] = [
                    b for b in msg["content"] if b.get("type") != "image_url"
                ]
                result.append(msg_copy)
            else:
                result.append(msg)
        return result

    return hook


def create_reply_hook(canvas: Canvas) -> Callable:
    def hook(messages: list[dict]) -> list[dict]:
        if not messages:
            return messages

        last = messages[-1]

        if _is_tool_message(last):
            return messages

        last_copy = dict(last)
        last_copy["content"] = _append_image(
            last_copy["content"], canvas.to_image_content()
        )

        return list(messages[:-1]) + [last_copy]

    return hook
