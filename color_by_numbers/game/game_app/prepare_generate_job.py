import threading
import time

from ...loading.rgb_image_loader import RgbImageLoader
from ...puzzle.generation_progress import GenerationProgress
from ...puzzle.puzzle_generator import PuzzleGenerator
from .download_work_detail import DownloadWorkDetail
from .prepare_job_title import PrepareJobTitle


class PrepareGenerateJob:
    """Background load/generate worker with progress reporting."""

    def __init__(
        self,
        *,
        image_loader: RgbImageLoader,
        generator: PuzzleGenerator,
        work_detail: DownloadWorkDetail | None = None,
        titles: PrepareJobTitle | None = None,
    ) -> None:
        self._image_loader = image_loader
        self._generator = generator
        self._work_detail = work_detail or DownloadWorkDetail()
        self._titles = titles or PrepareJobTitle()
        self.cancel_event: threading.Event | None = None
        self.thread: threading.Thread | None = None
        self.progress_lock = threading.Lock()
        self.latest_progress: dict[str, float | str | None] = {
            'fraction': 0.0,
            'message': 'Starting…',
            'eta': None,
            'work': '',
        }
        self.job_result: dict | None = None

    def is_running(self) -> bool:
        return self.thread is not None and self.thread.is_alive()

    def cancel(self) -> None:
        if self.cancel_event is not None:
            self.cancel_event.set()

    def start(
        self,
        *,
        n_colors: int,
        min_region_area: int | None,
        preserve_detail: bool,
        edge_aware: bool,
        max_regions: int | None,
        skin_bias: bool,
        locked_palette,
        on_rgb_loaded,
        rgb=None,
        url: str | None = None,
        path: str | None = None,
    ) -> str:
        """Start worker; returns loading title. Raises RuntimeError if busy."""
        if self.is_running():
            raise RuntimeError('Generation already running.')
        self.cancel_event = threading.Event()
        self.job_result = None
        include_download = url is not None
        tracker = GenerationProgress(include_download=include_download or path is not None)
        download_state = {'bytes': 0, 'total': None, 'started': None}
        title = self._titles.for_inputs(rgb=rgb, url=url, path=path)
        self.latest_progress = {
            'fraction': 0.0,
            'message': title,
            'eta': None,
            'work': '',
        }
        self.thread = threading.Thread(
            target=self._worker,
            kwargs={
                'rgb': rgb,
                'url': url,
                'path': path,
                'n_colors': n_colors,
                'min_region_area': min_region_area,
                'preserve_detail': preserve_detail,
                'edge_aware': edge_aware,
                'max_regions': max_regions,
                'skin_bias': skin_bias,
                'locked_palette': locked_palette,
                'tracker': tracker,
                'download_state': download_state,
                'on_rgb_loaded': on_rgb_loaded,
            },
            daemon=True,
        )
        self.thread.start()
        return title

    def take_result(self) -> dict | None:
        with self.progress_lock:
            result = self.job_result
            self.job_result = None
            return result

    def progress_snapshot(self) -> dict[str, float | str | None]:
        with self.progress_lock:
            return dict(self.latest_progress)

    def _report(
        self,
        download_state: dict,
        fraction: float,
        message: str,
        eta_seconds: float | None,
        _elapsed: float,
    ) -> None:
        with self.progress_lock:
            self.latest_progress = {
                'fraction': fraction,
                'message': message,
                'eta': eta_seconds,
                'work': self._work_detail.format_work_detail(download_state, message),
            }

    def _worker(
        self,
        *,
        rgb,
        url: str | None,
        path: str | None,
        n_colors: int,
        min_region_area: int | None,
        preserve_detail: bool,
        edge_aware: bool,
        max_regions: int | None,
        skin_bias: bool,
        locked_palette,
        tracker: GenerationProgress,
        download_state: dict,
        on_rgb_loaded,
    ) -> None:
        stop_pulse = threading.Event()

        def pulse_loop() -> None:
            while not stop_pulse.wait(0.15):
                self._report(download_state, *tracker.pulse())

        pulser = threading.Thread(target=pulse_loop, daemon=True)
        pulser.start()
        try:
            source = self._resolve_source(
                rgb=rgb,
                url=url,
                path=path,
                tracker=tracker,
                download_state=download_state,
                on_rgb_loaded=on_rgb_loaded,
            )
            puzzle = self._generator.generate(
                source,
                n_colors=n_colors if locked_palette is None else len(locked_palette),
                min_region_area=min_region_area,
                progress=lambda *args: self._report(download_state, *args),
                cancel_event=self.cancel_event,
                tracker=tracker,
                edge_aware=edge_aware,
                preserve_detail=preserve_detail,
                skin_bias=skin_bias,
                locked_palette=locked_palette,
                max_regions=max_regions,
            )
        except InterruptedError:
            with self.progress_lock:
                self.job_result = {'status': 'cancelled'}
            return
        except Exception as exc:  # noqa: BLE001 - show any generation failure in UI
            with self.progress_lock:
                self.job_result = {'status': 'error', 'error': exc}
            return
        finally:
            stop_pulse.set()
        with self.progress_lock:
            self.job_result = {
                'status': 'ready',
                'puzzle': puzzle,
                'tracker': tracker,
            }

    def _resolve_source(
        self,
        *,
        rgb,
        url: str | None,
        path: str | None,
        tracker: GenerationProgress,
        download_state: dict,
        on_rgb_loaded,
    ):
        source = rgb
        if url is not None:
            download_state['started'] = time.perf_counter()

            def on_download(downloaded: int, total: int | None) -> None:
                download_state['bytes'] = downloaded
                download_state['total'] = total
                self._report(download_state, *tracker.set_download_progress(downloaded, total))

            self._report(download_state, *tracker.set_download_progress(0, None))
            source = self._image_loader.load_from_url(url, progress=on_download)
            self._report(download_state, *tracker.complete_download())
            self._report(download_state, *tracker.complete_decode())
            on_rgb_loaded(source)
        elif path is not None:
            self._report(download_state, *tracker.set_download_progress(0, 1))
            source = self._image_loader.load_from_path(path)
            self._report(download_state, *tracker.set_download_progress(1, 1))
            self._report(download_state, *tracker.complete_download())
            self._report(download_state, *tracker.complete_decode())
            on_rgb_loaded(source)
        elif source is not None:
            self._report(download_state, *tracker.complete_decode())
        return source
