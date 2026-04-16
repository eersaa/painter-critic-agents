from PIL import Image

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
