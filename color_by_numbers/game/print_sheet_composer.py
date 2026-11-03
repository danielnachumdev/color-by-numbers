import numpy as np
from PIL import Image, ImageDraw

from ..puzzle.puzzle import Puzzle
from .print_page_layout import PaperSize, PrintPageLayout
from .sheet_font import SheetFont
from .sheet_renderer import SheetRenderer


class PrintSheetComposer:
    """Compose print pages: puzzle page + optional separate palette page."""

    def __init__(
        self,
        renderer: SheetRenderer | None = None,
        font_loader: SheetFont | None = None,
        layout: PrintPageLayout | None = None,
        cut_mark: int = 18,
    ) -> None:
        self._renderer = renderer or SheetRenderer(base_scale=3, min_side=1200)
        self._font_loader = font_loader or SheetFont()
        self._layout = layout or PrintPageLayout()
        self._cut_mark = cut_mark

    def compose_pages(
        self,
        puzzle: Puzzle,
        *,
        filled: bool = False,
        palette_on_second_page: bool = True,
        paper: PaperSize | None = None,
    ) -> list[np.ndarray]:
        if paper is not None:
            self._layout = PrintPageLayout(paper=paper, bleed_px=self._layout.bleed_px, safe_px=self._layout.safe_px)
        sheet = self._render_sheet(puzzle, filled=filled)
        if palette_on_second_page:
            puzzle_page = self._place_on_page(sheet)
            legend = self._legend_page(puzzle)
            return [puzzle_page, legend]
        legend = self._legend_strip(puzzle, sheet.shape[1])
        body = np.vstack([sheet, np.full((24, sheet.shape[1], 3), 255, dtype=np.uint8), legend])
        return [self._place_on_page(body)]

    def compose(self, puzzle: Puzzle, filled: bool = False) -> np.ndarray:
        return self.compose_pages(puzzle, filled=filled, palette_on_second_page=False)[0]

    def _render_sheet(self, puzzle: Puzzle, *, filled: bool) -> np.ndarray:
        previous = self._renderer.show_preview_overlay
        self._renderer.show_preview_overlay = filled
        try:
            return self._renderer.render(puzzle)
        finally:
            self._renderer.show_preview_overlay = previous

    def _place_on_page(self, body: np.ndarray) -> np.ndarray:
        target_w, target_h = self._layout.fit_size(body.shape[1], body.shape[0])
        fitted = np.asarray(
            Image.fromarray(body).resize((target_w, target_h), Image.Resampling.LANCZOS)
        )
        page = np.full((self._layout.paper.height_px, self._layout.paper.width_px, 3), 255, dtype=np.uint8)
        left, top, right, bottom = self._layout.content_box
        x = left + (right - left - fitted.shape[1]) // 2
        y = top + (bottom - top - fitted.shape[0]) // 2
        page[y : y + fitted.shape[0], x : x + fitted.shape[1]] = fitted
        return self._draw_guides(page, left, top, right, bottom)

    def _legend_page(self, puzzle: Puzzle) -> np.ndarray:
        width = self._layout.paper.width_px
        height = self._layout.paper.height_px
        image = Image.new('RGB', (width, height), (255, 255, 255))
        draw = ImageDraw.Draw(image)
        title = self._font_loader.load(36)
        body = self._font_loader.load(24)
        left, top, right, _bottom = self._layout.content_box
        draw.text((left, top), 'Palette', fill=(0, 0, 0), font=title)
        x, y = left, top + 56
        cell = 120
        for index, color in enumerate(puzzle.palette):
            draw.rectangle((x, y, x + 48, y + 48), fill=tuple(int(c) for c in color), outline=(0, 0, 0), width=2)
            draw.text((x + 60, y + 10), str(index + 1), fill=(0, 0, 0), font=body)
            x += cell
            if x > right - cell:
                x = left
                y += 72
        return self._draw_guides(np.asarray(image), *self._layout.content_box)

    def _legend_strip(self, puzzle: Puzzle, width: int) -> np.ndarray:
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

    def _draw_guides(self, page: np.ndarray, left: int, top: int, right: int, bottom: int) -> np.ndarray:
        image = Image.fromarray(page)
        draw = ImageDraw.Draw(image)
        mark = self._cut_mark
        ink = (40, 40, 40)
        bleed = self._layout.bleed_px
        pairs = [
            ((left, 0), (left, mark)),
            ((0, top), (mark, top)),
            ((right - 1, 0), (right - 1, mark)),
            ((page.shape[1] - mark, top), (page.shape[1], top)),
            ((left, page.shape[0] - mark), (left, page.shape[0])),
            ((0, bottom - 1), (mark, bottom - 1)),
            ((right - 1, page.shape[0] - mark), (right - 1, page.shape[0])),
            ((page.shape[1] - mark, bottom - 1), (page.shape[1], bottom - 1)),
            ((bleed, bleed), (bleed + mark, bleed)),
            ((bleed, bleed), (bleed, bleed + mark)),
        ]
        for start, end in pairs:
            draw.line([start, end], fill=ink, width=2)
        return np.asarray(image)
