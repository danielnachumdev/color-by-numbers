from pathlib import Path

import numpy as np
from PIL import Image

from ..puzzle.puzzle import Puzzle
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

    def export_png(self, path: str | Path, puzzle: Puzzle, *, print_ready: bool = True) -> None:
        sheet = self._compose(puzzle, print_ready=print_ready)
        Image.fromarray(sheet).save(path, format='PNG')

    def export_pdf(self, path: str | Path, puzzle: Puzzle, *, print_ready: bool = True) -> None:
        sheet = self._compose(puzzle, print_ready=print_ready)
        Image.fromarray(sheet).convert('RGB').save(path, format='PDF', resolution=150.0)

    def _compose(self, puzzle: Puzzle, *, print_ready: bool) -> np.ndarray:
        if print_ready:
            return self._composer.compose(puzzle, filled=False)
        sheet = self._renderer.render(puzzle)
        return sheet
