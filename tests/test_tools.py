import pytest

from painter_critic.canvas import Canvas
from painter_critic.tools import create_tools


@pytest.fixture
def canvas():
    return Canvas(100, 100)


@pytest.fixture
def tools(canvas):
    return create_tools(canvas)


@pytest.fixture
def draw_rectangle(tools):
    return tools[0]


@pytest.fixture
def draw_circle(tools):
    return tools[1]


@pytest.fixture
def draw_line(tools):
    return tools[2]


@pytest.fixture
def draw_polygon(tools):
    return tools[3]


class TestToolsFactory:
    def test_create_tools_returns_list_of_four(self, canvas):
        tools = create_tools(canvas)

        assert isinstance(tools, list)
        assert len(tools) == 4

    def test_create_tools_all_items_are_callable(self, canvas):
        tools = create_tools(canvas)

        for tool in tools:
            assert callable(tool)

    def test_create_tools_share_same_canvas(self, canvas):
        tools = create_tools(canvas)
        draw_rect, draw_circle, _, _ = tools

        draw_rect(10, 10, 20, 20, "#FF0000")
        draw_circle(50, 50, 5, "#0000FF")

        r1, g1, b1, _ = canvas.image.getpixel((15, 15))
        r2, g2, b2, _ = canvas.image.getpixel((50, 50))
        assert (r1, g1, b1) == (255, 0, 0)
        assert (r2, g2, b2) == (0, 0, 255)


class TestDrawRectangle:
    def test_draw_rectangle_fills_pixels_with_color(self, canvas, draw_rectangle):
        draw_rectangle(10, 10, 30, 30, "#FF0000")

        r, g, b, a = canvas.image.getpixel((20, 20))
        assert (r, g, b) == (255, 0, 0)
        assert a == 255

    def test_draw_rectangle_returns_success_string(self, draw_rectangle):
        result = draw_rectangle(10, 10, 30, 30, "#FF0000")

        assert isinstance(result, str)
        assert "error" not in result.lower()

    def test_draw_rectangle_does_not_fill_outside_bounds(self, canvas, draw_rectangle):
        draw_rectangle(10, 10, 20, 20, "#FF0000")

        pixel = canvas.image.getpixel((5, 5))
        assert pixel == (255, 255, 255, 255)

    def test_draw_rectangle_clamps_negative_coords(self, canvas, draw_rectangle):
        result = draw_rectangle(-10, -10, 20, 20, "#FF0000")

        assert "error" not in result.lower()
        r, g, b, _ = canvas.image.getpixel((0, 0))
        assert (r, g, b) == (255, 0, 0)

    def test_draw_rectangle_clamps_coords_exceeding_canvas(
        self, canvas, draw_rectangle
    ):
        result = draw_rectangle(80, 80, 200, 200, "#00FF00")

        assert "error" not in result.lower()
        r, g, b, _ = canvas.image.getpixel((99, 99))
        assert (r, g, b) == (0, 255, 0)

    def test_draw_rectangle_invalid_color_returns_error(self, draw_rectangle):
        result = draw_rectangle(10, 10, 30, 30, "red")

        assert "error" in result.lower()

    def test_draw_rectangle_never_raises(self, draw_rectangle):
        result = draw_rectangle(-999, -999, 9999, 9999, "not-a-color")

        assert isinstance(result, str)


class TestDrawCircle:
    def test_draw_circle_fills_center_pixel(self, canvas, draw_circle):
        draw_circle(50, 50, 10, "#0000FF")

        r, g, b, a = canvas.image.getpixel((50, 50))
        assert (r, g, b) == (0, 0, 255)
        assert a == 255

    def test_draw_circle_returns_success_string(self, draw_circle):
        result = draw_circle(50, 50, 10, "#0000FF")

        assert isinstance(result, str)
        assert "error" not in result.lower()

    def test_draw_circle_does_not_fill_distant_pixel(self, canvas, draw_circle):
        draw_circle(50, 50, 5, "#0000FF")

        pixel = canvas.image.getpixel((0, 0))
        assert pixel == (255, 255, 255, 255)

    def test_draw_circle_clamps_center_when_out_of_bounds(self, canvas, draw_circle):
        result = draw_circle(-10, 50, 15, "#FF0000")

        assert "error" not in result.lower()

    def test_draw_circle_clamps_center_exceeding_canvas(self, canvas, draw_circle):
        result = draw_circle(200, 50, 15, "#FF0000")

        assert "error" not in result.lower()

    def test_draw_circle_invalid_color_returns_error(self, draw_circle):
        result = draw_circle(50, 50, 10, "blue")

        assert "error" in result.lower()

    def test_draw_circle_never_raises(self, draw_circle):
        result = draw_circle(-999, -999, 9999, "not-a-color")

        assert isinstance(result, str)


class TestDrawLine:
    def test_draw_line_changes_pixels_along_path(self, canvas, draw_line):
        draw_line(0, 50, 99, 50, "#FF0000")

        r, g, b, _ = canvas.image.getpixel((50, 50))
        assert (r, g, b) == (255, 0, 0)

    def test_draw_line_returns_success_string(self, draw_line):
        result = draw_line(0, 0, 99, 99, "#FF0000")

        assert isinstance(result, str)
        assert "error" not in result.lower()

    def test_draw_line_default_width_is_one(self, canvas, draw_line):
        draw_line(0, 50, 99, 50, "#FF0000")

        on_line = canvas.image.getpixel((50, 50))
        above = canvas.image.getpixel((50, 45))
        assert on_line[0] == 255  # red channel
        assert above == (255, 255, 255, 255)

    def test_draw_line_custom_width_widens_stroke(self, canvas, draw_line):
        draw_line(0, 50, 99, 50, "#FF0000", width=10)

        r, g, b, _ = canvas.image.getpixel((50, 53))
        assert (r, g, b) == (255, 0, 0)

    def test_draw_line_clamps_out_of_bounds_coords(self, canvas, draw_line):
        result = draw_line(-50, 50, 200, 50, "#00FF00")

        assert "error" not in result.lower()

    def test_draw_line_invalid_color_returns_error(self, draw_line):
        result = draw_line(0, 0, 50, 50, "green")

        assert "error" in result.lower()

    def test_draw_line_never_raises(self, draw_line):
        result = draw_line(-999, -999, 9999, 9999, "bad", width=-1)

        assert isinstance(result, str)


class TestDrawPolygon:
    def test_draw_polygon_fills_interior_pixel(self, canvas, draw_polygon):
        points = [(10, 10), (50, 10), (30, 50)]
        draw_polygon(points, "#FF0000")

        r, g, b, _ = canvas.image.getpixel((30, 20))
        assert (r, g, b) == (255, 0, 0)

    def test_draw_polygon_returns_success_string(self, draw_polygon):
        points = [(10, 10), (50, 10), (30, 50)]
        result = draw_polygon(points, "#FF0000")

        assert isinstance(result, str)
        assert "error" not in result.lower()

    def test_draw_polygon_fewer_than_three_points_returns_error(self, draw_polygon):
        result = draw_polygon([(10, 10), (50, 50)], "#FF0000")

        assert "error" in result.lower()

    def test_draw_polygon_one_point_returns_error(self, draw_polygon):
        result = draw_polygon([(10, 10)], "#FF0000")

        assert "error" in result.lower()

    def test_draw_polygon_zero_points_returns_error(self, draw_polygon):
        result = draw_polygon([], "#FF0000")

        assert "error" in result.lower()

    def test_draw_polygon_clamps_out_of_bounds_coords(self, canvas, draw_polygon):
        points = [(-10, -10), (200, -10), (50, 200)]
        result = draw_polygon(points, "#00FF00")

        assert "error" not in result.lower()

    def test_draw_polygon_invalid_color_returns_error(self, draw_polygon):
        points = [(10, 10), (50, 10), (30, 50)]
        result = draw_polygon(points, "red")

        assert "error" in result.lower()

    def test_draw_polygon_never_raises(self, draw_polygon):
        result = draw_polygon([], "bad-color")

        assert isinstance(result, str)

    def test_draw_polygon_quad_fills_interior(self, canvas, draw_polygon):
        points = [(10, 10), (90, 10), (90, 90), (10, 90)]
        draw_polygon(points, "#0000FF")

        r, g, b, _ = canvas.image.getpixel((50, 50))
        assert (r, g, b) == (0, 0, 255)


VALID_COLORS = ["#FF0000", "#00ff00", "#0000FF", "#123456"]
INVALID_COLORS = ["red", "FF0000", "#GG0000", "#12345", "", "123"]


class TestColorValidation:
    @pytest.mark.parametrize("color", VALID_COLORS)
    def test_draw_rectangle_accepts_valid_hex_color(self, draw_rectangle, color):
        result = draw_rectangle(10, 10, 30, 30, color)

        assert "error" not in result.lower()

    @pytest.mark.parametrize("color", INVALID_COLORS)
    def test_draw_rectangle_rejects_invalid_color(self, draw_rectangle, color):
        result = draw_rectangle(10, 10, 30, 30, color)

        assert "error" in result.lower()

    @pytest.mark.parametrize("color", VALID_COLORS)
    def test_draw_circle_accepts_valid_hex_color(self, draw_circle, color):
        result = draw_circle(50, 50, 10, color)

        assert "error" not in result.lower()

    @pytest.mark.parametrize("color", INVALID_COLORS)
    def test_draw_circle_rejects_invalid_color(self, draw_circle, color):
        result = draw_circle(50, 50, 10, color)

        assert "error" in result.lower()

    @pytest.mark.parametrize("color", VALID_COLORS)
    def test_draw_line_accepts_valid_hex_color(self, draw_line, color):
        result = draw_line(0, 0, 50, 50, color)

        assert "error" not in result.lower()

    @pytest.mark.parametrize("color", INVALID_COLORS)
    def test_draw_line_rejects_invalid_color(self, draw_line, color):
        result = draw_line(0, 0, 50, 50, color)

        assert "error" in result.lower()

    @pytest.mark.parametrize("color", VALID_COLORS)
    def test_draw_polygon_accepts_valid_hex_color(self, draw_polygon, color):
        points = [(10, 10), (50, 10), (30, 50)]
        result = draw_polygon(points, color)

        assert "error" not in result.lower()

    @pytest.mark.parametrize("color", INVALID_COLORS)
    def test_draw_polygon_rejects_invalid_color(self, draw_polygon, color):
        points = [(10, 10), (50, 10), (30, 50)]
        result = draw_polygon(points, color)

        assert "error" in result.lower()
