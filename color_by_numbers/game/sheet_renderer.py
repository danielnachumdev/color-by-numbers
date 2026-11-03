import math

import cv2
import numpy as np
from PIL import Image, ImageDraw

from ..puzzle.puzzle import Puzzle
from .sheet_font import SheetFont


class SheetRenderer:
    def __init__(
        self,
        base_scale: int = 2,
        min_side: int = 720,
        line_width: int = 1,
        font_loader: SheetFont | None = None,
    ) -> None:
        self._base_scale = base_scale
        self._min_side = min_side
        self.line_width = line_width
        self._font_loader = font_loader or SheetFont()
        self.content_scale = 1
        self.highlight_color_id: int | None = None
        self.hint_region_id: int | None = None
        self.show_preview_overlay = False

    def render(self, puzzle: Puzzle) -> np.ndarray:
        height, width = puzzle.label_map.shape
        scale = self.choose_scale(height, width)
        self.content_scale = scale
        if self.show_preview_overlay:
            sheet = self._paint_preview(puzzle, scale)
        else:
            sheet = self._paint_fills(puzzle, scale)
            self._paint_highlight(sheet, puzzle, scale)
            self._paint_hint(sheet, puzzle, scale)
        self._paint_smooth_outlines(sheet, puzzle, scale)
        if not self.show_preview_overlay:
            sheet = self._paint_numbers(sheet, puzzle, scale)
        return sheet

    def choose_scale(self, height: int, width: int) -> int:
        longest = max(height, width)
        fitted = int(math.ceil(self._min_side / float(longest)))
        return max(self._base_scale, fitted)

    def thicken(self) -> None:
        self.line_width = min(6, self.line_width + 1)

    def thin(self) -> None:
        self.line_width = max(1, self.line_width - 1)

    def _paint_preview(self, puzzle: Puzzle, scale: int) -> np.ndarray:
        height, width = puzzle.preview.shape[:2]
        return cv2.resize(
            puzzle.preview,
            (width * scale, height * scale),
            interpolation=cv2.INTER_NEAREST,
        )

    def _paint_fills(self, puzzle: Puzzle, scale: int) -> np.ndarray:
        height, width = puzzle.label_map.shape
        sheet = np.full((height * scale, width * scale, 3), 255, dtype=np.uint8)
        upscaled = self._upscaled_labels(puzzle, scale)
        for region_id in puzzle.filled_regions:
            color_id = puzzle.region_color_id[region_id]
            sheet[upscaled == region_id] = puzzle.palette[color_id]
        return sheet

    def _paint_highlight(self, sheet: np.ndarray, puzzle: Puzzle, scale: int) -> None:
        if self.highlight_color_id is None:
            return
        upscaled = self._upscaled_labels(puzzle, scale)
        dim = (sheet.astype(np.float32) * 0.72 + 255 * 0.28).astype(np.uint8)
        keep = np.zeros(upscaled.shape, dtype=bool)
        for region_id, color_id in puzzle.region_color_id.items():
            if color_id == self.highlight_color_id and region_id not in puzzle.filled_regions:
                keep |= upscaled == region_id
        sheet[:] = np.where(keep[..., None], sheet, dim)

    def _paint_hint(self, sheet: np.ndarray, puzzle: Puzzle, scale: int) -> None:
        if self.hint_region_id is None:
            return
        upscaled = self._upscaled_labels(puzzle, scale)
        color = puzzle.palette[puzzle.region_color_id[self.hint_region_id]]
        tint = (color.astype(np.float32) * 0.45 + np.array([255, 255, 180]) * 0.55)
        mask = upscaled == self.hint_region_id
        sheet[mask] = tint.astype(np.uint8)

    def _upscaled_labels(self, puzzle: Puzzle, scale: int) -> np.ndarray:
        height, width = puzzle.label_map.shape
        return cv2.resize(
            puzzle.label_map.astype(np.float32),
            (width * scale, height * scale),
            interpolation=cv2.INTER_NEAREST,
        ).astype(np.int32)

    def _paint_smooth_outlines(self, sheet: np.ndarray, puzzle: Puzzle, scale: int) -> None:
        if puzzle.boundary_paths:
            self._draw_boundary_paths(sheet, puzzle, scale)
        else:
            self._draw_bitmap_outlines(sheet, puzzle, scale)
        self._draw_image_rectangle(sheet, puzzle, scale)

    def _draw_boundary_paths(self, sheet: np.ndarray, puzzle: Puzzle, scale: int) -> None:
        thickness = max(self.line_width, int(round(scale * 0.28)) + (self.line_width - 1))
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
        thickness = max(self.line_width, int(round(scale * 0.28)) + (self.line_width - 1))
        cv2.rectangle(
            sheet,
            (0, 0),
            (width * scale - 1, height * scale - 1),
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
