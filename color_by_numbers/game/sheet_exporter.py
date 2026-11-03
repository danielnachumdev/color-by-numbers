from pathlib import Path

import numpy as np
from PIL import Image

from ..puzzle.puzzle import Puzzle
from .print_page_layout import PrintPageLayout
from .print_sheet_composer import PrintSheetComposer
from .sheet_renderer import SheetRenderer


class SheetExporter:
    def __init__(
        self,
        renderer: SheetRenderer | None = None,
        composer: PrintSheetComposer | None = None,
    ) -> None:
        self._renderer = renderer or SheetRenderer()
        self._composer = composer or PrintSheetComposer(renderer=self._renderer)

    def export_png(
        self,
        path: str | Path,
        puzzle: Puzzle,
        *,
        print_ready: bool = True,
        filled: bool = False,
        paper: str = 'A4',
    ) -> None:
        pages = self._pages(puzzle, print_ready=print_ready, filled=filled, paper=paper, multi=False)
        Image.fromarray(pages[0]).save(path, format='PNG')

    def export_pdf(
        self,
        path: str | Path,
        puzzle: Puzzle,
        *,
        print_ready: bool = True,
        filled: bool = False,
        paper: str = 'A4',
        palette_on_second_page: bool = True,
    ) -> None:
        pages = self._pages(
            puzzle,
            print_ready=print_ready,
            filled=filled,
            paper=paper,
            multi=palette_on_second_page,
        )
        images = [Image.fromarray(page).convert('RGB') for page in pages]
        first, rest = images[0], images[1:]
        first.save(path, format='PDF', resolution=150.0, save_all=True, append_images=rest)

    def export_completed_png(self, path: str | Path, puzzle: Puzzle) -> None:
        self.export_png(path, puzzle, print_ready=True, filled=True)

    def _pages(
        self,
        puzzle: Puzzle,
        *,
        print_ready: bool,
        filled: bool,
        paper: str,
        multi: bool,
    ) -> list[np.ndarray]:
        if not print_ready:
            previous = self._renderer.show_preview_overlay
            self._renderer.show_preview_overlay = filled
            try:
                return [self._renderer.render(puzzle)]
            finally:
                self._renderer.show_preview_overlay = previous
        paper_size = PrintPageLayout.LETTER if paper.lower() == 'letter' else PrintPageLayout.A4
        return self._composer.compose_pages(
            puzzle,
            filled=filled,
            palette_on_second_page=multi,
            paper=paper_size,
        )
