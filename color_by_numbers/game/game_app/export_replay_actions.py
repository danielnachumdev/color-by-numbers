from tkinter import filedialog, messagebox


class ExportReplayActions:
    def __init__(self, host) -> None:
        self._host = host

    def export_png(self) -> None:
        host = self._host
        if host._puzzle is None:
            return
        path = filedialog.asksaveasfilename(defaultextension='.png', filetypes=[('PNG', '*.png')])
        if path:
            host._exporter.export_png(
                path,
                host._puzzle,
                print_ready=True,
                paper=host._paper_size.get(),
            )
            host._settings.set('paper', host._paper_size.get())

    def export_pdf(self) -> None:
        host = self._host
        if host._puzzle is None:
            return
        path = filedialog.asksaveasfilename(defaultextension='.pdf', filetypes=[('PDF', '*.pdf')])
        if path:
            host._exporter.export_pdf(
                path,
                host._puzzle,
                print_ready=True,
                paper=host._paper_size.get(),
                palette_on_second_page=True,
            )
            host._settings.set('paper', host._paper_size.get())

    def export_completed(self) -> None:
        host = self._host
        if host._puzzle is None:
            return
        path = filedialog.asksaveasfilename(defaultextension='.png', filetypes=[('PNG', '*.png')])
        if path:
            host._exporter.export_completed_png(path, host._puzzle)

    def replay_fills(self) -> None:
        host = self._host
        if host._puzzle is None or not host._puzzle.fill_history:
            messagebox.showinfo(host._strings.t('app_title'), 'No fill history to replay.')
            return
        frames = host._puzzle.replay_frames()
        original = set(host._puzzle.filled_regions)
        host._puzzle.filled_regions = set()
        host._canvas.redraw()

        def step(index: int) -> None:
            if index >= len(frames):
                host._puzzle.filled_regions = original
                host._canvas.redraw()
                host._presentation.sync_palette_remaining()
                host._presentation.update_status()
                return
            host._puzzle.filled_regions = set(frames[index])
            host._canvas.redraw()
            host._root.after(120, lambda: step(index + 1))

        step(0)
