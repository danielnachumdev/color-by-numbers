from tkinter import messagebox

from ...puzzle.generation_progress import GenerationProgress


class LoadingJobController:
    def __init__(self, host) -> None:
        self._host = host

    def start_prepare_job(
        self,
        rgb=None,
        url: str | None = None,
        path: str | None = None,
    ) -> None:
        host = self._host
        try:
            title = host._prepare_job.start(
                n_colors=int(host._n_colors.get()),
                min_region_area=host._min_region_area,
                preserve_detail=host._preserve_detail,
                edge_aware=host._edge_aware.get(),
                max_regions=host._max_regions,
                skin_bias=host._skin_bias,
                locked_palette=host._locked_palette if host._lock_palette.get() else None,
                on_rgb_loaded=host._set_rgb,
                rgb=rgb,
                url=url,
                path=path,
            )
        except RuntimeError:
            messagebox.showinfo('Color by Numbers', 'Generation already running.')
            return
        host._loading.show(title)
        host._status.set(title)
        self.schedule_tick()

    def schedule_tick(self) -> None:
        host = self._host
        if host._loading_tick_scheduled:
            return
        host._loading_tick_scheduled = True
        host._root.after(100, self.on_tick)

    def on_tick(self) -> None:
        host = self._host
        host._loading_tick_scheduled = False
        if not host._loading.visible:
            return
        result = host._prepare_job.take_result()
        if result is not None:
            self.apply_result(result)
            return
        snapshot = host._prepare_job.progress_snapshot()
        message = str(snapshot['message'])
        fraction = float(snapshot['fraction'] or 0.0)
        eta = snapshot['eta']
        eta_value = float(eta) if isinstance(eta, (int, float)) else None
        work = str(snapshot.get('work') or '')
        host._status.set(message)
        host._loading.set_progress(fraction, message, eta_value, work_detail=work)
        self.schedule_tick()

    def apply_result(self, result: dict) -> None:
        host = self._host
        status = result.get('status')
        if status == 'cancelled':
            self.on_cancelled()
            return
        if status == 'error':
            self.on_failed(result['error'])
            return
        tracker = result.get('tracker')
        if isinstance(tracker, GenerationProgress):
            fraction, message, eta, _elapsed = tracker.finish()
            host._loading.set_progress(fraction, message, eta)
            host._root.update_idletasks()
        host._presentation.show_puzzle(result['puzzle'])

    def set_detail(self, message: str) -> None:
        host = self._host
        host._status.set(message)
        host._loading.set_detail(message)

    def on_cancelled(self) -> None:
        host = self._host
        host._loading.hide()
        host._status.set('Generation cancelled')

    def on_failed(self, exc: Exception) -> None:
        host = self._host
        host._loading.hide()
        host._status.set('Generation failed')
        messagebox.showerror('Color by Numbers', str(exc))

    def cancel(self) -> None:
        host = self._host
        if host._prepare_job.cancel_event is not None:
            host._prepare_job.cancel()
            self.set_detail('Cancelling…')
