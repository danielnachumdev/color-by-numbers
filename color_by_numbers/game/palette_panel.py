import tkinter as tk

import numpy as np


class PalettePanel(tk.Frame):
    def __init__(self, master, on_select) -> None:
        super().__init__(master)
        self._on_select = on_select
        self._selected = 0
        self._buttons: list[tk.Button] = []

    def set_palette(self, palette: np.ndarray) -> None:
        for button in self._buttons:
            button.destroy()
        self._buttons.clear()
        self._selected = 0
        for index, color in enumerate(palette):
            hex_color = self._to_hex(color)
            button = tk.Button(
                self,
                text=str(index + 1),
                bg=hex_color,
                fg=self._contrast_text(color),
                width=4,
                command=lambda i=index: self._select(i),
            )
            button.pack(side=tk.LEFT, padx=2, pady=2)
            self._buttons.append(button)
        if len(palette) > 0:
            self._select(0)

    def selected_index(self) -> int:
        return self._selected

    def _select(self, index: int) -> None:
        self._selected = index
        for i, button in enumerate(self._buttons):
            button.configure(relief=tk.SUNKEN if i == index else tk.RAISED)
        self._on_select(index)

    def _to_hex(self, color: np.ndarray) -> str:
        r, g, b = (int(channel) for channel in color)
        return f'#{r:02x}{g:02x}{b:02x}'

    def _contrast_text(self, color: np.ndarray) -> str:
        luminance = 0.299 * color[0] + 0.587 * color[1] + 0.114 * color[2]
        return '#000000' if luminance > 140 else '#ffffff'
