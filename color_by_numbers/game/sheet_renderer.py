import numpy as np

from ..puzzle.puzzle import Puzzle


class SheetRenderer:
    def render(self, puzzle: Puzzle) -> np.ndarray:
        height, width = puzzle.label_map.shape
        sheet = np.full((height, width, 3), 255, dtype=np.uint8)
        self._paint_filled_regions(sheet, puzzle)
        self._paint_outlines(sheet, puzzle)
        return sheet

    def _paint_filled_regions(self, sheet: np.ndarray, puzzle: Puzzle) -> None:
        for region_id in puzzle.filled_regions:
            color_id = puzzle.region_color_id[region_id]
            sheet[puzzle.label_map == region_id] = puzzle.palette[color_id]

    def _paint_outlines(self, sheet: np.ndarray, puzzle: Puzzle) -> None:
        sheet[puzzle.outlines.astype(bool)] = (0, 0, 0)
