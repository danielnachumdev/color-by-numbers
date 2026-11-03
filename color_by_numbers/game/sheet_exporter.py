from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw

from ..puzzle.puzzle import Puzzle
from .sheet_font import SheetFont
from .sheet_renderer import SheetRenderer


class SheetExporter:
    def __init__(
        self,
        renderer: SheetRenderer | None = None,
        font_loader: SheetFont | None = None,
    ) -> None:
        self._renderer = renderer or SheetRenderer()
        self._font_loader = font_loader or SheetFont()

    def export_png(self, path: str | Path, puzzle: Puzzle) -> None:
        sheet = self._compose(puzzle)
        Image.fromarray(sheet).save(path, format='PNG')

    def export_pdf(self, path: str | Path, puzzle: Puzzle) -> None:
        sheet = self._compose(puzzle)
        Image.fromarray(sheet).convert('RGB').save(path, format='PDF', resolution=150.0)

    def _compose(self, puzzle: Puzzle) -> np.ndarray:
        sheet = self._renderer.render(puzzle)
        legend = self._legend_strip(puzzle, sheet.shape[1])
        return np.vstack([sheet, legend])

    def _legend_strip(self, puzzle: Puzzle, width: int) -> np.ndarray:
        height = 72
        strip = np.full((height, width, 3), 255, dtype=np.uint8)
        image = Image.fromarray(strip)
        draw = ImageDraw.Draw(image)
        font = self._font_loader.load(18)
        x = 12
        for index, color in enumerate(puzzle.palette):
            draw.rectangle((x, 16, x + 28, 44), fill=tuple(int(c) for c in color), outline=(0, 0, 0))
            draw.text((x + 34, 20), str(index + 1), fill=(0, 0, 0), font=font)
            x += 70
            if x > width - 70:
                break
        return np.asarray(image)
