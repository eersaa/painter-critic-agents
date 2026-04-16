import re
from collections.abc import Callable

from painter_critic.canvas import Canvas

_COLOR_RE = re.compile(r"^#[0-9A-Fa-f]{6}$")


def _valid_color(color: str) -> bool:
    return bool(_COLOR_RE.match(color))


def _clamp(value: int, lo: int, hi: int) -> int:
    return max(lo, min(hi, value))


def create_tools(canvas: Canvas) -> list[Callable]:
    width, height = canvas.size
    max_x = width - 1
    max_y = height - 1

    def draw_rectangle(x1, y1, x2, y2, color):
        if not _valid_color(color):
            return f"error: invalid color '{color}'"
        x1 = _clamp(int(x1), 0, max_x)
        y1 = _clamp(int(y1), 0, max_y)
        x2 = _clamp(int(x2), 0, max_x)
        y2 = _clamp(int(y2), 0, max_y)
        canvas.draw().rectangle([x1, y1, x2, y2], fill=color)
        return f"rectangle drawn at ({x1},{y1})-({x2},{y2}) with color {color}"

    def draw_circle(cx, cy, radius, color):
        if not _valid_color(color):
            return f"error: invalid color '{color}'"
        cx = _clamp(int(cx), 0, max_x)
        cy = _clamp(int(cy), 0, max_y)
        radius = int(radius)
        x1 = _clamp(cx - radius, 0, max_x)
        y1 = _clamp(cy - radius, 0, max_y)
        x2 = _clamp(cx + radius, 0, max_x)
        y2 = _clamp(cy + radius, 0, max_y)
        canvas.draw().ellipse([x1, y1, x2, y2], fill=color)
        return f"circle drawn at center ({cx},{cy}) radius {radius} with color {color}"

    def draw_line(x1, y1, x2, y2, color, width=1):
        if not _valid_color(color):
            return f"error: invalid color '{color}'"
        x1 = _clamp(int(x1), 0, max_x)
        y1 = _clamp(int(y1), 0, max_y)
        x2 = _clamp(int(x2), 0, max_x)
        y2 = _clamp(int(y2), 0, max_y)
        w = max(1, int(width)) if width is not None else 1
        canvas.draw().line([x1, y1, x2, y2], fill=color, width=w)
        return (
            f"line drawn from ({x1},{y1}) to ({x2},{y2}) with color {color} width {w}"
        )

    def draw_polygon(points, color):
        if not _valid_color(color):
            return f"error: invalid color '{color}'"
        if len(points) < 3:
            return f"error: polygon requires at least 3 points, got {len(points)}"
        clamped = [
            (_clamp(int(x), 0, max_x), _clamp(int(y), 0, max_y)) for x, y in points
        ]
        canvas.draw().polygon(clamped, fill=color)
        return f"polygon drawn with {len(clamped)} points and color {color}"

    return [draw_rectangle, draw_circle, draw_line, draw_polygon]
