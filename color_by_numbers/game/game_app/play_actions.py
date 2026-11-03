from tkinter import messagebox


class PlayActions:
    def __init__(self, host) -> None:
        self._host = host

    def on_canvas_click(self, x: int, y: int) -> None:
        host = self._host
        if host._puzzle is None:
            return
        selected = host._palette.selected_index()
        region_id = host._puzzle.try_fill(x, y, selected)
        if region_id is None:
            return
        host._timer.record_fill()
        host._sound.fill_success()
        if not host._paint_mode.get():
            host._canvas.flash_fill()
        host._canvas.set_hint_region(None)
        if host._puzzle.is_complete():
            self.finish_puzzle()
            return
        if host._puzzle.color_is_complete(selected):
            nxt = host._puzzle.next_incomplete_color(selected)
            if nxt is not None:
                host._palette.select(nxt)
        host._presentation.sync_palette_remaining()
        host._canvas.redraw()
        host._presentation.refresh_highlight()
        host._presentation.update_status()
        host._sessions_ui.schedule_autosave()

    def finish_puzzle(self) -> None:
        host = self._host
        host._timer.stop()
        host._sound.puzzle_complete()
        host._canvas.show_preview(host._puzzle)
        summary = host._timer.summary(len(host._puzzle.region_color_id))
        host._status.set(f'{host._strings.t("complete")}  {summary}')
        messagebox.showinfo(
            host._strings.t('app_title'),
            f'{host._strings.t("complete")}\n{summary}',
        )

    def undo(self) -> None:
        host = self._host
        if host._puzzle is None or host._puzzle.undo() is None:
            return
        host._presentation.sync_palette_remaining()
        host._canvas.redraw()
        host._presentation.refresh_highlight()
        host._presentation.update_status()
        host._sessions_ui.schedule_autosave()

    def redo(self) -> None:
        host = self._host
        if host._puzzle is None or host._puzzle.redo() is None:
            return
        host._presentation.sync_palette_remaining()
        host._canvas.redraw()
        host._presentation.refresh_highlight()
        host._presentation.update_status()
        host._sessions_ui.schedule_autosave()

    def hint(self) -> None:
        host = self._host
        if host._puzzle is None:
            return
        candidates = host._puzzle.unfilled_regions_for_color(host._palette.selected_index())
        if not candidates:
            messagebox.showinfo('Color by Numbers', 'No remaining regions for this color.')
            return
        region_id = candidates[0]
        host._canvas.set_hint_region(region_id)
        host._root.after(900, lambda: host._canvas.set_hint_region(None))
