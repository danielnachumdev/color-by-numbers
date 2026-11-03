import tkinter as tk

import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageTk

from .canvas_view_transform import CanvasViewTransform
from .sheet_renderer import SheetRenderer


class PuzzleCanvas(tk.Canvas):
    _ZOOM_STEP = 1.15

    def __init__(self, master, on_click) -> None:
        super().__init__(master, background='white', highlightthickness=0)
        self._on_click = on_click
        self._renderer = SheetRenderer()
        self._view = CanvasViewTransform()
        self._photo = None
        self._source_rgb: np.ndarray | None = None
        self._puzzle = None
        self._last_size = (0, 0)
        self._pan_last: tuple[int, int] | None = None
        self._bind_interactions()

    def show_puzzle(self, puzzle) -> None:
        self._puzzle = puzzle
        self._view.reset()
        self.redraw()

    def show_preview(self, puzzle) -> None:
        self._puzzle = puzzle
        self._view.reset()
        self._draw_array(puzzle.preview)

    def redraw(self) -> None:
        if self._puzzle is None:
            return
        sheet = self._renderer.render(self._puzzle)
        sheet = self._draw_numbers(sheet, self._puzzle)
        self._draw_array(sheet)

    def zoom_in(self) -> None:
        self._sync_viewport_size()
        self._view.zoom_toward_center(self._ZOOM_STEP)
        self._refresh_display()

    def zoom_out(self) -> None:
        self._sync_viewport_size()
        self._view.zoom_toward_center(1.0 / self._ZOOM_STEP)
        self._refresh_display()

    def reset_zoom(self) -> None:
        self._view.reset()
        self._refresh_display()

    def _bind_interactions(self) -> None:
        self.bind('<Button-1>', self._handle_click)
        self.bind('<Configure>', self._handle_configure)
        self.bind('<MouseWheel>', self._handle_mousewheel)
        self.bind('<Control-MouseWheel>', self._handle_mousewheel)
        self.bind('<Button-4>', self._handle_linux_zoom_in)
        self.bind('<Button-5>', self._handle_linux_zoom_out)
        self.bind('<Control-Button-4>', self._handle_linux_zoom_in)
        self.bind('<Control-Button-5>', self._handle_linux_zoom_out)
        self.bind('<ButtonPress-2>', self._start_pan)
        self.bind('<B2-Motion>', self._continue_pan)
        self.bind('<ButtonRelease-2>', self._end_pan)

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
        self._source_rgb = rgb
        height, width = rgb.shape[:2]
        self._view.set_content_size(width, height)
        self._sync_viewport_size()
        self._refresh_display()

    def _refresh_display(self) -> None:
        if self._source_rgb is None:
            return
        displayed_width, displayed_height = self._view.displayed_size()
        image = Image.fromarray(self._source_rgb).resize(
            (displayed_width, displayed_height),
            Image.NEAREST,
        )
        self._photo = ImageTk.PhotoImage(image)
        self.delete('all')
        origin_x, origin_y = self._view.image_origin()
        self.create_image(origin_x, origin_y, anchor=tk.NW, image=self._photo)

    def _sync_viewport_size(self) -> None:
        width = max(1, self.winfo_width())
        height = max(1, self.winfo_height())
        self._view.set_viewport_size(width, height)
        self._last_size = (width, height)

    def _handle_configure(self, _event) -> None:
        size = (max(1, self.winfo_width()), max(1, self.winfo_height()))
        if size == self._last_size:
            return
        self._view.set_viewport_size(*size)
        self._last_size = size
        self._refresh_display()

    def _handle_click(self, event) -> None:
        if self._puzzle is None:
            return
        mapped = self._view.canvas_to_content(event.x, event.y)
        if mapped is None:
            return
        self._on_click(*mapped)

    def _handle_mousewheel(self, event) -> None:
        if event.delta == 0:
            return
        factor = self._ZOOM_STEP if event.delta > 0 else 1.0 / self._ZOOM_STEP
        self._view.zoom_by(factor, event.x, event.y)
        self._refresh_display()

    def _handle_linux_zoom_in(self, event) -> None:
        self._view.zoom_by(self._ZOOM_STEP, event.x, event.y)
        self._refresh_display()

    def _handle_linux_zoom_out(self, event) -> None:
        self._view.zoom_by(1.0 / self._ZOOM_STEP, event.x, event.y)
        self._refresh_display()

    def _start_pan(self, event) -> None:
        self._pan_last = (event.x, event.y)

    def _continue_pan(self, event) -> None:
        if self._pan_last is None:
            return
        last_x, last_y = self._pan_last
        self._view.pan_by(event.x - last_x, event.y - last_y)
        self._pan_last = (event.x, event.y)
        self._refresh_display()

    def _end_pan(self, _event) -> None:
        self._pan_last = None
