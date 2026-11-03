import time
import tkinter as tk
from tkinter import ttk


class LoadingOverlay:
    _SLOW_AFTER_SECONDS = 2.0

    def __init__(self, parent: tk.Misc) -> None:
        self._parent = parent
        self._frame = tk.Frame(parent, bg='#1a1a1a')
        self._center = tk.Frame(self._frame, bg='#1a1a1a')
        self._center.place(relx=0.5, rely=0.5, anchor='center')
        self._label = tk.Label(
            self._center,
            text='Generating puzzle…',
            fg='white',
            bg='#1a1a1a',
            font=('DejaVu Sans', 16),
        )
        self._label.pack(pady=(0, 12))
        self._bar = ttk.Progressbar(
            self._center,
            mode='determinate',
            length=320,
            maximum=1000,
        )
        self._bar.pack(pady=8)
        self._detail = tk.Label(self._center, text='', fg='#cccccc', bg='#1a1a1a')
        self._detail.pack(pady=(4, 0))
        self._work = tk.Label(self._center, text='', fg='#bbbbbb', bg='#1a1a1a')
        self._work.pack(pady=(4, 0))
        self._timing = tk.Label(self._center, text='', fg='#aaaaaa', bg='#1a1a1a')
        self._timing.pack(pady=(8, 0))
        self._warning = tk.Label(self._center, text='', fg='#f0c674', bg='#1a1a1a')
        self._warning.pack(pady=(6, 0))
        self._visible = False
        self._started_at = 0.0

    def show(self, message: str = 'Generating puzzle…') -> None:
        self._label.configure(text=message)
        self._detail.configure(text='')
        self._work.configure(text='')
        self._timing.configure(text='Elapsed 0.0s')
        self._warning.configure(text='')
        self._bar['value'] = 0
        self._started_at = time.perf_counter()
        if not self._visible:
            self._frame.place(relx=0, rely=0, relwidth=1, relheight=1)
            self._frame.lift()
            self._visible = True
        self._parent.configure(cursor='watch')

    def set_progress(
        self,
        fraction: float,
        detail: str,
        eta_seconds: float | None,
        elapsed_seconds: float | None = None,
        work_detail: str = '',
    ) -> None:
        clamped = max(0.0, min(1.0, fraction))
        self._bar['value'] = int(round(clamped * 1000))
        percent = int(round(clamped * 100))
        self._label.configure(text=detail)
        self._detail.configure(text=f'{percent}% complete')
        self._work.configure(text=work_detail)
        elapsed = (
            elapsed_seconds
            if elapsed_seconds is not None
            else time.perf_counter() - self._started_at
        )
        self._timing.configure(text=self._format_timing(elapsed, eta_seconds))
        if elapsed >= self._SLOW_AFTER_SECONDS and clamped < 0.99:
            self._warning.configure(text='Taking longer than usual…')
        else:
            self._warning.configure(text='')

    def set_detail(self, message: str) -> None:
        self._detail.configure(text=message)

    def hide(self) -> None:
        if self._visible:
            self._frame.place_forget()
            self._visible = False
        self._bar['value'] = 0
        self._warning.configure(text='')
        self._parent.configure(cursor='')

    @property
    def visible(self) -> bool:
        return self._visible

    def _format_timing(self, elapsed: float, eta_seconds: float | None) -> str:
        elapsed_text = f'Elapsed {elapsed:.1f}s'
        if eta_seconds is None:
            return f'{elapsed_text}  ·  Estimating remaining…'
        if eta_seconds < 60:
            return f'{elapsed_text}  ·  About {max(1, int(round(eta_seconds)))}s remaining'
        minutes = int(eta_seconds // 60)
        seconds = int(round(eta_seconds % 60))
        return f'{elapsed_text}  ·  About {minutes}m {seconds:02d}s remaining'
