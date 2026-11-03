import tkinter as tk

import numpy as np


class PalettePanel(tk.Frame):
    def __init__(self, master, on_select) -> None:
        super().__init__(master)
        self._on_select = on_select
        self._selected = 0
        self._buttons: list[tk.Button] = []
        self._remaining: dict[int, int] = {}

    def set_palette(self, palette: np.ndarray, remaining: dict[int, int] | None = None) -> None:
        for button in self._buttons:
            button.destroy()
        self._buttons.clear()
        self._selected = 0
        self._remaining = remaining or {}
        for index, color in enumerate(palette):
            hex_color = self._to_hex(color)
            left = self._remaining.get(index)
            label = str(index + 1) if left is None else f'{index + 1}:{left}'
            button = tk.Button(
                self,
                text=label,
                bg=hex_color,
                fg=self._contrast_text(color),
                width=5,
                command=lambda i=index: self.select(i),
            )
            button.pack(side=tk.LEFT, padx=2, pady=2)
            self._buttons.append(button)
        if len(palette) > 0:
            self.select(0)

    def update_remaining(self, remaining: dict[int, int]) -> None:
        self._remaining = remaining
        for index, button in enumerate(self._buttons):
            left = remaining.get(index, 0)
            button.configure(text=f'{index + 1}:{left}')

    def selected_index(self) -> int:
        return self._selected

    def select(self, index: int, notify: bool = True) -> None:
        if index < 0 or index >= len(self._buttons):
            return
        self._selected = index
        for i, button in enumerate(self._buttons):
            button.configure(relief=tk.SUNKEN if i == index else tk.RAISED)
        if notify:
            self._on_select(index)

    def _to_hex(self, color: np.ndarray) -> str:
        r, g, b = (int(channel) for channel in color)
        return f'#{r:02x}{g:02x}{b:02x}'

    def _contrast_text(self, color: np.ndarray) -> str:
        luminance = 0.299 * color[0] + 0.587 * color[1] + 0.114 * color[2]
        return '#000000' if luminance > 140 else '#ffffff'
