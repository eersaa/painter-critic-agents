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
            if "tool_calls" in message or message.get("role") == "tool":
                return message

            result = dict(message)
            content = result["content"]

            if isinstance(content, list):
                result["content"] = list(content) + [canvas.to_image_content()]
            else:
                result["content"] = [
                    {"type": "text", "text": content},
                    canvas.to_image_content(),
                ]

            return result

        return message

    return hook


def create_reply_hook(canvas: Canvas) -> Callable:
    def hook(messages: list[dict]) -> list[dict]:
        if not messages:
            return messages

        last = messages[-1]

        if "tool_calls" in last or last.get("role") == "tool":
            return messages

        last_copy = dict(last)
        content = last_copy["content"]

        if isinstance(content, list):
            last_copy["content"] = list(content) + [canvas.to_image_content()]
        else:
            last_copy["content"] = [
                {"type": "text", "text": content},
                canvas.to_image_content(),
            ]

        return list(messages[:-1]) + [last_copy]

    return hook
