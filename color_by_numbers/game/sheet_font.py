from functools import lru_cache

from PIL import ImageFont


@lru_cache(maxsize=16)
def _truetype_font(size: int) -> ImageFont.ImageFont:
    candidates = (
        'DejaVuSans.ttf',
        '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',
        '/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf',
        'Arial.ttf',
    )
    for path in candidates:
        try:
            return ImageFont.truetype(path, size=max(8, size))
        except OSError:
            continue
    return ImageFont.load_default()


class SheetFont:
    def load(self, size: int) -> ImageFont.ImageFont:
        return _truetype_font(size)