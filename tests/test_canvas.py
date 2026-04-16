import base64

import pytest
from PIL import Image, ImageDraw

from painter_critic.canvas import Canvas


class TestCanvasAcceptance:
    def test_canvas_default_creates_200x200_white_rgba_image(self):
        canvas = Canvas()

        assert canvas.size == (200, 200)
        assert canvas.image.mode == "RGBA"
        assert canvas.image.getpixel((0, 0)) == (255, 255, 255, 255)
        assert canvas.image.getpixel((199, 199)) == (255, 255, 255, 255)

    def test_canvas_draw_paints_pixels_on_image(self):
        canvas = Canvas()

        draw = canvas.draw()
        draw.rectangle([40, 40, 60, 60], fill="red")

        assert canvas.image.getpixel((50, 50)) == (255, 0, 0, 255)

    def test_canvas_save_writes_valid_png_preserving_content(self, tmp_output_dir):
        canvas = Canvas()
        draw = canvas.draw()
        draw.ellipse([10, 10, 50, 50], fill="blue")

        path = tmp_output_dir / "test.png"
        canvas.save(path)

        saved = Image.open(path)
        assert saved.size == (200, 200)
        r, g, b = saved.convert("RGB").getpixel((30, 30))
        assert (r, g, b) == (0, 0, 255)

    def test_canvas_to_image_content_returns_openai_vision_format(self):
        canvas = Canvas()

        result = canvas.to_image_content()

        assert result["type"] == "image_url"
        url = result["image_url"]["url"]
        assert url.startswith("data:image/png;base64,")


class TestCanvasUnit:
    # -- Constructor --

    def test_canvas_custom_size_returns_correct_dimensions(self):
        canvas = Canvas(100, 50)

        assert canvas.size == (100, 50)

    def test_canvas_custom_background_fills_with_specified_color(self):
        canvas = Canvas(background="red")

        r, g, b, a = canvas.image.getpixel((0, 0))
        assert (r, g, b) == (255, 0, 0)

    def test_canvas_negative_width_raises_value_error(self):
        with pytest.raises(ValueError):
            Canvas(-1, 200)

    def test_canvas_negative_height_raises_value_error(self):
        with pytest.raises(ValueError):
            Canvas(200, -1)

    def test_canvas_zero_width_raises_value_error(self):
        with pytest.raises(ValueError):
            Canvas(0, 200)

    def test_canvas_zero_height_raises_value_error(self):
        with pytest.raises(ValueError):
            Canvas(200, 0)

    # -- draw() --

    def test_canvas_draw_returns_image_draw_instance(self):
        canvas = Canvas()

        draw = canvas.draw()

        assert isinstance(draw, ImageDraw.ImageDraw)

    def test_canvas_draw_rectangle_changes_target_pixels(self):
        canvas = Canvas(100, 100, background="white")

        draw = canvas.draw()
        draw.rectangle([10, 10, 20, 20], fill="green")

        r, g, b, _a = canvas.image.getpixel((15, 15))
        assert (r, g, b) == (0, 128, 0)

    # -- save() --

    def test_canvas_save_preserves_dimensions_after_roundtrip(self, tmp_path):
        canvas = Canvas(150, 75)
        path = tmp_path / "roundtrip.png"

        canvas.save(path)

        loaded = Image.open(path)
        assert loaded.size == (150, 75)

    def test_canvas_save_accepts_pathlib_path(self, tmp_path):
        canvas = Canvas()
        path = tmp_path / "pathlib_test.png"

        canvas.save(path)

        assert path.exists()

    def test_canvas_save_creates_nested_parent_directories(self, tmp_path):
        canvas = Canvas()
        path = tmp_path / "a" / "b" / "out.png"

        canvas.save(path)

        assert path.exists()

    # -- to_base64() --

    def test_canvas_to_base64_returns_string(self):
        canvas = Canvas()

        result = canvas.to_base64()

        assert isinstance(result, str)

    def test_canvas_to_base64_decodes_to_png_magic_bytes(self):
        canvas = Canvas()

        result = canvas.to_base64()
        raw = base64.b64decode(result)

        assert raw[:4] == b"\x89PNG"

    def test_canvas_to_base64_changes_after_drawing(self):
        canvas = Canvas()
        blank_b64 = canvas.to_base64()

        draw = canvas.draw()
        draw.rectangle([0, 0, 100, 100], fill="blue")
        drawn_b64 = canvas.to_base64()

        assert blank_b64 != drawn_b64

    # -- to_image_content() --

    def test_canvas_to_image_content_type_equals_image_url(self):
        canvas = Canvas()

        result = canvas.to_image_content()

        assert result["type"] == "image_url"

    def test_canvas_to_image_content_url_starts_with_data_uri_prefix(self):
        canvas = Canvas()

        result = canvas.to_image_content()
        url = result["image_url"]["url"]

        assert url.startswith("data:image/png;base64,")

    def test_canvas_to_image_content_base64_matches_to_base64(self):
        canvas = Canvas()

        b64 = canvas.to_base64()
        url = canvas.to_image_content()["image_url"]["url"]
        url_b64 = url.removeprefix("data:image/png;base64,")

        assert url_b64 == b64

    # -- Mutability --

    def test_canvas_multiple_draw_calls_modify_same_image(self):
        canvas = Canvas(100, 100, background="white")

        draw1 = canvas.draw()
        draw1.rectangle([10, 10, 20, 20], fill="red")

        draw2 = canvas.draw()
        draw2.rectangle([50, 50, 60, 60], fill="blue")

        r1, g1, b1, _a1 = canvas.image.getpixel((15, 15))
        r2, g2, b2, _a2 = canvas.image.getpixel((55, 55))
        assert (r1, g1, b1) == (255, 0, 0)
        assert (r2, g2, b2) == (0, 0, 255)
