from tkinter import messagebox


class PuzzlePresentation:
    def __init__(self, host) -> None:
        self._host = host

    def show_puzzle(self, puzzle) -> None:
        host = self._host
        host._loading.hide()
        host._puzzle = puzzle
        host._timer.reset()
        host._timer.start()
        host._canvas.set_number_scale(1.6 if host._kids_mode else 1.0)
        remaining = {
            index: puzzle.remaining_for_color(index)
            for index in range(len(puzzle.palette))
        }
        display = host._color_blind.remap(puzzle.palette, host._color_mode.get())
        host._palette.set_palette(display, remaining)
        host._canvas.set_display_palette(display)
        host._canvas.show_puzzle(puzzle)
        self.refresh_highlight()
        self.sync_paint_mode()
        self.update_status()
        host._sessions_ui.schedule_autosave()

    def on_palette_select(self, index: int) -> None:
        self.refresh_highlight()
        self.update_status()

    def refresh_highlight(self) -> None:
        host = self._host
        if host._puzzle is None:
            return
        color_id = host._palette.selected_index() if host._highlight_current.get() else None
        host._canvas.set_highlight_color(color_id)

    def sync_paint_mode(self) -> None:
        host = self._host
        enabled = host._paint_mode.get()
        host._canvas.set_paint_mode(enabled)
        host._settings.set('paint_mode', enabled)

    def toggle_palette_lock(self) -> None:
        host = self._host
        if host._lock_palette.get():
            if host._puzzle is None:
                host._lock_palette.set(False)
                messagebox.showinfo(
                    'Color by Numbers',
                    'Generate a puzzle before locking its palette.',
                )
                return
            host._locked_palette = host._puzzle.palette.copy()
            host._status.set('Palette locked for next generate')
        else:
            host._locked_palette = None

    def apply_color_mode(self) -> None:
        host = self._host
        host._settings.set('color_mode', host._color_mode.get())
        if host._puzzle is None:
            return
        display = host._color_blind.remap(host._puzzle.palette, host._color_mode.get())
        remaining = {
            index: host._puzzle.remaining_for_color(index)
            for index in range(len(host._puzzle.palette))
        }
        selected = host._palette.selected_index()
        host._palette.set_palette(display, remaining)
        host._palette.select(selected, notify=False)
        host._canvas.set_display_palette(display)
        self.refresh_highlight()

    def sync_palette_remaining(self) -> None:
        host = self._host
        if host._puzzle is None:
            return
        remaining = {
            index: host._puzzle.remaining_for_color(index)
            for index in range(len(host._puzzle.palette))
        }
        host._palette.update_remaining(remaining)

    def update_status(self) -> None:
        host = self._host
        if host._puzzle is None:
            return
        base = host._puzzle.status_summary(host._palette.selected_index())
        timer = host._timer.summary(len(host._puzzle.region_color_id))
        history = len(host._puzzle.fill_history)
        host._status.set(f'{base}  ·  {timer}  ·  fills {history}')
