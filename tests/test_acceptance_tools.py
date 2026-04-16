from painter_critic.canvas import Canvas
from painter_critic.tools import create_tools


class TestToolsAcceptance:
    def test_tools_draw_rectangle_modifies_canvas_and_returns_string(self):
        canvas = Canvas()
        before = canvas.to_base64()
        draw_rectangle, _, _, _ = create_tools(canvas)

        result = draw_rectangle(10, 10, 50, 50, "#FF0000")

        assert canvas.to_base64() != before
        assert isinstance(result, str) and len(result) > 0

    def test_tools_draw_circle_modifies_canvas_and_returns_string(self):
        canvas = Canvas()
        before = canvas.to_base64()
        _, draw_circle, _, _ = create_tools(canvas)

        result = draw_circle(100, 100, 20, "#00FF00")

        assert canvas.to_base64() != before
        assert isinstance(result, str) and len(result) > 0

    def test_tools_draw_line_modifies_canvas_and_returns_string(self):
        canvas = Canvas()
        before = canvas.to_base64()
        _, _, draw_line, _ = create_tools(canvas)

        result = draw_line(0, 150, 199, 150, "#0000FF")

        assert canvas.to_base64() != before
        assert isinstance(result, str) and len(result) > 0

    def test_tools_draw_polygon_modifies_canvas_and_returns_string(self):
        canvas = Canvas()
        before = canvas.to_base64()
        _, _, _, draw_polygon = create_tools(canvas)

        result = draw_polygon([(160, 10), (180, 40), (140, 40)], "#FFFF00")

        assert canvas.to_base64() != before
        assert isinstance(result, str) and len(result) > 0
