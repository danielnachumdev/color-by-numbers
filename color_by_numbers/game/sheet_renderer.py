import math

import cv2
import numpy as np
from PIL import Image, ImageDraw

from ..puzzle.puzzle import Puzzle
from .sheet_font import SheetFont


class SheetRenderer:
    def __init__(
        self,
        base_scale: int = 3,
        min_side: int = 1000,
        line_width: int = 1,
        font_loader: SheetFont | None = None,
    ) -> None:
        self._base_scale = base_scale
        self._min_side = min_side
        self._line_width = line_width
        self._font_loader = font_loader or SheetFont()
        self.content_scale = 1

    def render(self, puzzle: Puzzle) -> np.ndarray:
        height, width = puzzle.label_map.shape
        scale = self.choose_scale(height, width)
        self.content_scale = scale
        sheet = self._paint_fills(puzzle, scale)
        self._paint_smooth_outlines(sheet, puzzle, scale)
        return self._paint_numbers(sheet, puzzle, scale)

    def choose_scale(self, height: int, width: int) -> int:
        longest = max(height, width)
        fitted = int(math.ceil(self._min_side / float(longest)))
        return max(self._base_scale, fitted)

    def _paint_fills(self, puzzle: Puzzle, scale: int) -> np.ndarray:
        height, width = puzzle.label_map.shape
        sheet = np.full((height * scale, width * scale, 3), 255, dtype=np.uint8)
        upscaled = cv2.resize(
            puzzle.label_map.astype(np.float32),
            (width * scale, height * scale),
            interpolation=cv2.INTER_NEAREST,
        ).astype(np.int32)
        for region_id in puzzle.filled_regions:
            color_id = puzzle.region_color_id[region_id]
            sheet[upscaled == region_id] = puzzle.palette[color_id]
        return sheet

    def _paint_smooth_outlines(self, sheet: np.ndarray, puzzle: Puzzle, scale: int) -> None:
        if puzzle.boundary_paths:
            self._draw_boundary_paths(sheet, puzzle, scale)
        else:
            self._draw_bitmap_outlines(sheet, puzzle, scale)
        self._draw_image_rectangle(sheet, puzzle, scale)

    def _draw_boundary_paths(self, sheet: np.ndarray, puzzle: Puzzle, scale: int) -> None:
        thickness = max(self._line_width, int(round(scale * 0.35)))
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

    def _draw_image_rectangle(self, sheet: np.ndarray, puzzle: Puzzle, scale: int) -> None:
        height, width = puzzle.label_map.shape
        thickness = max(self._line_width, int(round(scale * 0.35)))
        top_left = (0, 0)
        bottom_right = (width * scale - 1, height * scale - 1)
        cv2.rectangle(
            sheet,
            top_left,
            bottom_right,
            color=(0, 0, 0),
            thickness=thickness,
            lineType=cv2.LINE_AA,
        )

    def _draw_bitmap_outlines(self, sheet: np.ndarray, puzzle: Puzzle, scale: int) -> None:
        mask = cv2.resize(
            puzzle.outlines.astype(np.uint8),
            (sheet.shape[1], sheet.shape[0]),
            interpolation=cv2.INTER_NEAREST,
        ).astype(bool)
        sheet[mask] = (0, 0, 0)

    def _paint_numbers(self, sheet: np.ndarray, puzzle: Puzzle, scale: int) -> np.ndarray:
        image = Image.fromarray(sheet)
        draw = ImageDraw.Draw(image)
        font = self._font_loader.load(max(12, 7 * scale))
        for region_id, (x, y) in puzzle.number_anchors.items():
            if region_id in puzzle.filled_regions:
                continue
            text = str(puzzle.player_number(region_id))
            anchor_x = int(x * scale)
            anchor_y = int(y * scale)
            bbox = draw.textbbox((0, 0), text, font=font)
            text_width = bbox[2] - bbox[0]
            text_height = bbox[3] - bbox[1]
            draw.text(
                (anchor_x - text_width // 2, anchor_y - text_height // 2),
                text,
                fill=(0, 0, 0),
                font=font,
            )
        return np.asarray(image)
