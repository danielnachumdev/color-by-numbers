import tkinter as tk
from tkinter import filedialog, messagebox, simpledialog

from ..loading.rgb_image_loader import RgbImageLoader
from ..puzzle.puzzle_generator import PuzzleGenerator
from .palette_panel import PalettePanel
from .puzzle_canvas import PuzzleCanvas
from .screen_window_geometry import ScreenWindowGeometry


class GameApp:
    def __init__(
        self,
        generator: PuzzleGenerator | None = None,
        image_loader: RgbImageLoader | None = None,
        window_geometry: ScreenWindowGeometry | None = None,
    ) -> None:
        self._generator = generator or PuzzleGenerator()
        self._image_loader = image_loader or RgbImageLoader()
        self._window_geometry = window_geometry or ScreenWindowGeometry()
        self._puzzle = None
        self._rgb = None
        self._root = tk.Tk()
        self._root.title('Color by Numbers')
        self._n_colors = tk.IntVar(value=8)
        self._status = tk.StringVar(value='Open an image or URL to start')
        self._apply_initial_geometry()
        self._build_layout()

    def run(self) -> None:
        self._root.mainloop()

    def _apply_initial_geometry(self) -> None:
        self._root.update_idletasks()
        geometry = self._window_geometry.geometry_string(
            self._root.winfo_screenwidth(),
            self._root.winfo_screenheight(),
        )
        self._root.geometry(geometry)
        self._root.minsize(640, 480)

    def _build_layout(self) -> None:
        toolbar = tk.Frame(self._root)
        toolbar.pack(fill=tk.X, padx=8, pady=8)
        self._build_file_controls(toolbar)
        tk.Label(self._root, textvariable=self._status).pack(fill=tk.X, padx=8)
        self._canvas = PuzzleCanvas(self._root, on_click=self._on_canvas_click)
        self._canvas.pack(fill=tk.BOTH, expand=True, padx=8, pady=8)
        self._build_zoom_controls(toolbar)
        self._palette = PalettePanel(self._root, on_select=self._on_palette_select)
        self._palette.pack(fill=tk.X, padx=8, pady=8)

    def _build_file_controls(self, toolbar: tk.Frame) -> None:
        tk.Button(toolbar, text='Open image…', command=self._open_image).pack(side=tk.LEFT)
        tk.Button(toolbar, text='Open URL…', command=self._open_url).pack(side=tk.LEFT, padx=4)
        tk.Button(toolbar, text='New puzzle', command=self._regenerate).pack(side=tk.LEFT, padx=4)
        tk.Label(toolbar, text='Colors:').pack(side=tk.LEFT, padx=(12, 2))
        tk.Spinbox(toolbar, from_=2, to=16, width=4, textvariable=self._n_colors).pack(side=tk.LEFT)

    def _build_zoom_controls(self, toolbar: tk.Frame) -> None:
        tk.Button(toolbar, text='Zoom −', command=self._canvas.zoom_out).pack(side=tk.RIGHT)
        tk.Button(toolbar, text='Zoom +', command=self._canvas.zoom_in).pack(side=tk.RIGHT, padx=4)
        tk.Button(toolbar, text='Fit', command=self._canvas.reset_zoom).pack(side=tk.RIGHT, padx=4)

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
        try:
            self._rgb = self._image_loader.load_from_path(path)
        except ValueError as exc:
            messagebox.showerror('Color by Numbers', str(exc))
            return
        self._regenerate()

    def _open_url(self) -> None:
        url = simpledialog.askstring(
            'Open URL',
            'Image URL (http:// or https://):',
            parent=self._root,
        )
        if not url:
            return
        self._status.set('Downloading image…')
        self._root.update_idletasks()
        try:
            self._rgb = self._image_loader.load_from_url(url)
        except (ValueError, ConnectionError, TimeoutError, OSError) as exc:
            self._status.set('Open an image or URL to start')
            messagebox.showerror('Color by Numbers', str(exc))
            return
        self._regenerate()

    def _regenerate(self) -> None:
        if self._rgb is None:
            messagebox.showinfo('Color by Numbers', 'Open an image or URL first.')
            return
        self._puzzle = self._generator.generate(self._rgb, n_colors=int(self._n_colors.get()))
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
