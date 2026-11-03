import numpy as np
from PIL import Image, ImageDraw

from ..puzzle.puzzle import Puzzle
from .sheet_font import SheetFont
from .sheet_renderer import SheetRenderer


class PrintSheetComposer:
    """Compose a print-ready page: margins, cut marks, puzzle sheet, and palette legend."""

    def __init__(
        self,
        renderer: SheetRenderer | None = None,
        font_loader: SheetFont | None = None,
        margin: int = 48,
        cut_mark: int = 18,
    ) -> None:
        self._renderer = renderer or SheetRenderer(base_scale=3, min_side=1200)
        self._font_loader = font_loader or SheetFont()
        self._margin = margin
        self._cut_mark = cut_mark

    def compose(self, puzzle: Puzzle, filled: bool = False) -> np.ndarray:
        previous_preview = self._renderer.show_preview_overlay
        self._renderer.show_preview_overlay = filled
        try:
            sheet = self._renderer.render(puzzle)
        finally:
            self._renderer.show_preview_overlay = previous_preview
        legend = self._legend(puzzle, sheet.shape[1])
        body = np.vstack([sheet, np.full((24, sheet.shape[1], 3), 255, dtype=np.uint8), legend])
        return self._frame_page(body)

    def _legend(self, puzzle: Puzzle, width: int) -> np.ndarray:
        rows = max(1, (len(puzzle.palette) + 7) // 8)
        height = 28 + rows * 44
        image = Image.new('RGB', (width, height), (255, 255, 255))
        draw = ImageDraw.Draw(image)
        title = self._font_loader.load(22)
        body = self._font_loader.load(18)
        draw.text((8, 4), 'Palette', fill=(0, 0, 0), font=title)
        x, y = 8, 32
        for index, color in enumerate(puzzle.palette):
            draw.rectangle((x, y, x + 28, y + 28), fill=tuple(int(c) for c in color), outline=(0, 0, 0))
            draw.text((x + 34, y + 4), str(index + 1), fill=(0, 0, 0), font=body)
            x += 90
            if x > width - 90:
                x = 8
                y += 44
        return np.asarray(image)

    def _frame_page(self, body: np.ndarray) -> np.ndarray:
        margin = self._margin
        mark = self._cut_mark
        height = body.shape[0] + margin * 2
        width = body.shape[1] + margin * 2
        page = np.full((height, width, 3), 255, dtype=np.uint8)
        page[margin : margin + body.shape[0], margin : margin + body.shape[1]] = body
        page = self._draw_cut_marks(page, margin, mark)
        return page

    def _draw_cut_marks(self, page: np.ndarray, margin: int, mark: int) -> np.ndarray:
        image = Image.fromarray(page)
        draw = ImageDraw.Draw(image)
        width, height = image.size
        ink = (40, 40, 40)
        pairs = [
            ((margin, 0), (margin, mark)),
            ((0, margin), (mark, margin)),
            ((width - margin - 1, 0), (width - margin - 1, mark)),
            ((width - mark, margin), (width, margin)),
            ((margin, height - mark), (margin, height)),
            ((0, height - margin - 1), (mark, height - margin - 1)),
            ((width - margin - 1, height - mark), (width - margin - 1, height)),
            ((width - mark, height - margin - 1), (width, height - margin - 1)),
        ]
        for start, end in pairs:
            draw.line([start, end], fill=ink, width=2)
        return np.asarray(image)
