import cv2
import numpy as np

from ..puzzle.puzzle import Puzzle


class SheetOutlinePainter:
    def paint(self, sheet: np.ndarray, puzzle: Puzzle, scale: int, line_width: int) -> None:
        if puzzle.boundary_paths:
            self.draw_boundary_paths(sheet, puzzle, scale, line_width)
        else:
            self.draw_bitmap_outlines(sheet, puzzle)
        self.draw_image_rectangle(sheet, puzzle, scale, line_width)

    def draw_boundary_paths(
        self,
        sheet: np.ndarray,
        puzzle: Puzzle,
        scale: int,
        line_width: int,
    ) -> None:
        thickness = max(line_width, int(round(scale * 0.28)) + (line_width - 1))
        for points in puzzle.boundary_paths:
            if len(points) < 2:
                continue
            closed = np.allclose(points[0], points[-1])
            scaled = np.round(points * scale).astype(np.int32).reshape(-1, 1, 2)
            cv2.polylines(
                sheet,
                [scaled],
                isClosed=closed,
                color=(0, 0, 0),
                thickness=thickness,
                lineType=cv2.LINE_AA,
            )

    def draw_image_rectangle(
        self,
        sheet: np.ndarray,
        puzzle: Puzzle,
        scale: int,
        line_width: int,
    ) -> None:
        height, width = puzzle.label_map.shape
        thickness = max(line_width, int(round(scale * 0.28)) + (line_width - 1))
        cv2.rectangle(
            sheet,
            (0, 0),
            (width * scale - 1, height * scale - 1),
            color=(0, 0, 0),
            thickness=thickness,
            lineType=cv2.LINE_AA,
        )

    def draw_bitmap_outlines(self, sheet: np.ndarray, puzzle: Puzzle) -> None:
        mask = cv2.resize(
            puzzle.outlines.astype(np.uint8),
            (sheet.shape[1], sheet.shape[0]),
            interpolation=cv2.INTER_NEAREST,
        ).astype(bool)
        sheet[mask] = (0, 0, 0)
