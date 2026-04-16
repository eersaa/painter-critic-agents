import base64
from io import BytesIO
from pathlib import Path

from PIL import Image, ImageDraw


class Canvas:
    def __init__(self, width=200, height=200, background="white"):
        if width <= 0:
            raise ValueError(f"width must be > 0, got {width}")
        if height <= 0:
            raise ValueError(f"height must be > 0, got {height}")
        self._image = Image.new("RGBA", (width, height), background)

    @property
    def size(self) -> tuple[int, int]:
        return self._image.size

    @property
    def image(self) -> Image.Image:
        return self._image

    def draw(self) -> ImageDraw.ImageDraw:
        return ImageDraw.Draw(self._image)

    def save(self, path) -> None:
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        self._image.save(str(path), format="PNG")

    def to_base64(self) -> str:
        buf = BytesIO()
        self._image.save(buf, format="PNG")
        return base64.b64encode(buf.getvalue()).decode()

    def to_image_content(self) -> dict:
        return {
            "type": "image_url",
            "image_url": {"url": f"data:image/png;base64,{self.to_base64()}"},
        }
