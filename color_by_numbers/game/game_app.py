import tkinter as tk
from tkinter import filedialog, messagebox

from ..helpers import read_rgb
from ..puzzle.puzzle_generator import PuzzleGenerator
from .palette_panel import PalettePanel
from .puzzle_canvas import PuzzleCanvas


class GameApp:
    def __init__(self, generator: PuzzleGenerator | None = None) -> None:
        self._generator = generator or PuzzleGenerator()
        self._puzzle = None
        self._image_path = None
        self._root = tk.Tk()
        self._root.title('Color by Numbers')
        self._n_colors = tk.IntVar(value=8)
        self._status = tk.StringVar(value='Open an image to start')
        self._build_layout()

    def run(self) -> None:
        self._root.mainloop()

    def _build_layout(self) -> None:
        toolbar = tk.Frame(self._root)
        toolbar.pack(fill=tk.X, padx=8, pady=8)
        tk.Button(toolbar, text='Open image…', command=self._open_image).pack(side=tk.LEFT)
        tk.Button(toolbar, text='New puzzle', command=self._regenerate).pack(side=tk.LEFT, padx=4)
        tk.Label(toolbar, text='Colors:').pack(side=tk.LEFT, padx=(12, 2))
        tk.Spinbox(toolbar, from_=2, to=16, width=4, textvariable=self._n_colors).pack(side=tk.LEFT)
        tk.Label(self._root, textvariable=self._status).pack(fill=tk.X, padx=8)
        self._canvas = PuzzleCanvas(self._root, on_click=self._on_canvas_click)
        self._canvas.pack(padx=8, pady=8)
        self._palette = PalettePanel(self._root, on_select=self._on_palette_select)
        self._palette.pack(fill=tk.X, padx=8, pady=8)

    def _open_image(self) -> None:
        path = filedialog.askopenfilename(
            title='Choose a photo',
            filetypes=[
                ('Images', '*.jpg *.jpeg *.png *.bmp *.webp'),
                ('All files', '*.*'),
            ],
        )
        if not path:
            return
        self._image_path = path
        self._regenerate()

    def _regenerate(self) -> None:
        if not self._image_path:
            messagebox.showinfo('Color by Numbers', 'Open an image first.')
            return
        rgb = read_rgb(self._image_path)
        self._puzzle = self._generator.generate(rgb, n_colors=int(self._n_colors.get()))
        self._palette.set_palette(self._puzzle.palette)
        self._canvas.show_puzzle(self._puzzle)
        self._update_status()

    def _on_palette_select(self, index: int) -> None:
        self._status.set(f'Selected color {index + 1}')
        if self._puzzle is not None:
            filled, total = self._puzzle.progress()
            self._status.set(f'Selected color {index + 1} — {filled}/{total} filled')

    def _on_canvas_click(self, x: int, y: int) -> None:
        if self._puzzle is None:
            return
        filled = self._puzzle.try_fill(x, y, self._palette.selected_index())
        if not filled:
            return
        if self._puzzle.is_complete():
            self._canvas.show_preview(self._puzzle)
            self._status.set('Complete!')
            messagebox.showinfo('Color by Numbers', 'Puzzle complete!')
            return
        self._canvas.redraw()
        self._update_status()

    def _update_status(self) -> None:
        if self._puzzle is None:
            return
        filled, total = self._puzzle.progress()
        selected = self._palette.selected_index() + 1
        self._status.set(f'Selected color {selected} — {filled}/{total} filled')
