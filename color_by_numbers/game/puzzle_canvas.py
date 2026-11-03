import tkinter as tk

import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageTk

from .sheet_renderer import SheetRenderer


class PuzzleCanvas(tk.Canvas):
    def __init__(self, master, on_click) -> None:
        super().__init__(master, background='white', highlightthickness=0)
        self._on_click = on_click
        self._renderer = SheetRenderer()
        self._photo = None
        self._puzzle = None
        self._scale = 1.0
        self.bind('<Button-1>', self._handle_click)

    def show_puzzle(self, puzzle) -> None:
        self._puzzle = puzzle
        self.redraw()

    def show_preview(self, puzzle) -> None:
        self._puzzle = puzzle
        self._draw_array(puzzle.preview)

    def redraw(self) -> None:
        if self._puzzle is None:
            return
        sheet = self._renderer.render(self._puzzle)
        sheet = self._draw_numbers(sheet, self._puzzle)
        self._draw_array(sheet)

    def _draw_numbers(self, sheet: np.ndarray, puzzle) -> np.ndarray:
        image = Image.fromarray(sheet)
        draw = ImageDraw.Draw(image)
        font = ImageFont.load_default()
        for region_id, (x, y) in puzzle.number_anchors.items():
            if region_id in puzzle.filled_regions:
                continue
            text = str(puzzle.player_number(region_id))
            draw.text((x - 3, y - 5), text, fill=(0, 0, 0), font=font)
        return np.asarray(image)

    def _draw_array(self, rgb: np.ndarray) -> None:
        height, width = rgb.shape[:2]
        max_display = 700
        scale = min(1.0, max_display / max(height, width))
        self._scale = scale
        image = Image.fromarray(rgb)
        if scale < 1.0:
            image = image.resize(
                (int(width * scale), int(height * scale)),
                Image.NEAREST,
            )
        self._photo = ImageTk.PhotoImage(image)
        self.delete('all')
        self.config(width=image.width, height=image.height)
        self.create_image(0, 0, anchor=tk.NW, image=self._photo)

    def _handle_click(self, event) -> None:
        if self._puzzle is None or self._scale <= 0:
            return
        x = int(event.x / self._scale)
        y = int(event.y / self._scale)
        self._on_click(x, y)
