import tkinter as tk
from tkinter import ttk

from ..difficulty_preset import DifficultyPresets


class ToolbarBuilder:
    def __init__(self, host) -> None:
        self._host = host

    def build_file_controls(self, toolbar: tk.Frame) -> None:
        host = self._host
        tk.Button(toolbar, text='Open image…', command=host._sources.open_image).pack(side=tk.LEFT)
        tk.Button(toolbar, text='Open URL…', command=host._sources.open_url).pack(
            side=tk.LEFT, padx=4
        )
        tk.Button(toolbar, text='Paste', command=host._sources.paste_clipboard).pack(
            side=tk.LEFT, padx=4
        )
        tk.Button(toolbar, text='Webcam', command=host._sources.capture_webcam).pack(
            side=tk.LEFT, padx=4
        )
        tk.Button(toolbar, text='New puzzle', command=host._sources.regenerate).pack(
            side=tk.LEFT, padx=4
        )
        tk.Button(toolbar, text='Cancel', command=host._loading_job.cancel).pack(
            side=tk.LEFT, padx=4
        )
        tk.Label(toolbar, text='Preset:').pack(side=tk.LEFT, padx=(12, 2))
        host._preset = ttk.Combobox(
            toolbar,
            values=[preset.name for preset in DifficultyPresets.all()],
            width=8,
            state='readonly',
        )
        host._preset.set(DifficultyPresets.NORMAL.name)
        host._preset.bind('<<ComboboxSelected>>', host._apply_preset)
        host._preset.pack(side=tk.LEFT)
        tk.Label(toolbar, text='Colors:').pack(side=tk.LEFT, padx=(12, 2))
        tk.Spinbox(toolbar, from_=2, to=16, width=4, textvariable=host._n_colors).pack(side=tk.LEFT)

    def build_play_controls(self, toolbar: tk.Frame) -> None:
        host = self._host
        tk.Button(toolbar, text='Undo', command=host._play.undo).pack(side=tk.LEFT, padx=(12, 2))
        tk.Button(toolbar, text='Redo', command=host._play.redo).pack(side=tk.LEFT, padx=2)
        tk.Button(toolbar, text='Hint', command=host._play.hint).pack(side=tk.LEFT, padx=2)
        tk.Button(
            toolbar,
            text='Lines −',
            command=lambda: host._canvas.thin_lines(),
        ).pack(side=tk.LEFT, padx=(12, 2))
        tk.Button(
            toolbar,
            text='Lines +',
            command=lambda: host._canvas.thicken_lines(),
        ).pack(side=tk.LEFT, padx=2)

    def build_zoom_controls(self, toolbar: tk.Frame) -> None:
        host = self._host
        tk.Button(toolbar, text='Zoom −', command=host._canvas.zoom_out).pack(side=tk.RIGHT)
        tk.Button(toolbar, text='Zoom +', command=host._canvas.zoom_in).pack(side=tk.RIGHT, padx=4)
        tk.Button(toolbar, text='100%', command=host._canvas.zoom_100).pack(side=tk.RIGHT, padx=4)
        tk.Button(toolbar, text='Fit', command=host._canvas.reset_zoom).pack(side=tk.RIGHT, padx=4)
