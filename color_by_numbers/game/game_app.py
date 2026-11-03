import threading
import time
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox, simpledialog
from tkinter import ttk

from ..loading.rgb_image_loader import RgbImageLoader
from ..persistence.puzzle_session import PuzzleSession
from ..persistence.recent_sources import RecentSources
from ..puzzle.generation_progress import GenerationProgress
from ..puzzle.puzzle_generator import PuzzleGenerator
from .difficulty_preset import DifficultyPreset, DifficultyPresets
from .feedback_sound import FeedbackSound
from .loading_overlay import LoadingOverlay
from .palette_panel import PalettePanel
from .puzzle_canvas import PuzzleCanvas
from .screen_window_geometry import ScreenWindowGeometry
from .sheet_exporter import SheetExporter


class GameApp:
    def __init__(
        self,
        generator: PuzzleGenerator | None = None,
        image_loader: RgbImageLoader | None = None,
        window_geometry: ScreenWindowGeometry | None = None,
        recent_sources: RecentSources | None = None,
        session_store: PuzzleSession | None = None,
        exporter: SheetExporter | None = None,
    ) -> None:
        self._generator = generator or PuzzleGenerator()
        self._image_loader = image_loader or RgbImageLoader()
        self._window_geometry = window_geometry or ScreenWindowGeometry()
        self._recents = recent_sources or RecentSources()
        self._sessions = session_store or PuzzleSession()
        self._exporter = exporter or SheetExporter()
        self._puzzle = None
        self._rgb = None
        self._source_kind = None
        self._source_value = None
        self._min_region_area: int | None = None
        self._cancel_event: threading.Event | None = None
        self._generate_thread: threading.Thread | None = None
        self._progress_lock = threading.Lock()
        self._latest_progress: dict[str, float | str | None] = {
            'fraction': 0.0,
            'message': 'Starting…',
            'eta': None,
            'work': '',
        }
        self._job_result: dict | None = None
        self._loading_tick_scheduled = False
        self._root = tk.Tk()
        self._root.title('Color by Numbers')
        self._n_colors = tk.IntVar(value=8)
        self._status = tk.StringVar(value='Open an image or URL to start')
        self._highlight_current = tk.BooleanVar(value=True)
        self._sound = FeedbackSound(self._root)
        self._apply_initial_geometry()
        self._build_layout()
        self._bind_shortcuts()
        self._enable_drag_and_drop()

    def run(self) -> None:
        self._root.mainloop()

    def _apply_initial_geometry(self) -> None:
        self._root.update_idletasks()
        geometry = self._window_geometry.geometry_string(
            self._root.winfo_screenwidth(),
            self._root.winfo_screenheight(),
        )
        self._root.geometry(geometry)
        self._root.minsize(720, 520)

    def _build_layout(self) -> None:
        self._build_menu()
        toolbar = tk.Frame(self._root)
        toolbar.pack(fill=tk.X, padx=8, pady=4)
        self._build_file_controls(toolbar)
        self._build_play_controls(toolbar)
        tk.Label(self._root, textvariable=self._status).pack(fill=tk.X, padx=8)
        self._canvas = PuzzleCanvas(self._root, on_click=self._on_canvas_click)
        self._canvas.pack(fill=tk.BOTH, expand=True, padx=8, pady=8)
        self._loading = LoadingOverlay(self._root)
        self._build_zoom_controls(toolbar)
        self._palette = PalettePanel(self._root, on_select=self._on_palette_select)
        self._palette.pack(fill=tk.X, padx=8, pady=8)

    def _build_menu(self) -> None:
        menubar = tk.Menu(self._root)
        file_menu = tk.Menu(menubar, tearoff=0)
        file_menu.add_command(label='Open image…', command=self._open_image)
        file_menu.add_command(label='Open URL…', command=self._open_url)
        file_menu.add_command(label='Recent…', command=self._open_recent)
        file_menu.add_separator()
        file_menu.add_command(label='Save progress…', command=self._save_session)
        file_menu.add_command(label='Load progress…', command=self._load_session)
        file_menu.add_command(label='Export PNG…', command=self._export_png)
        file_menu.add_command(label='Export PDF…', command=self._export_pdf)
        menubar.add_cascade(label='File', menu=file_menu)
        play_menu = tk.Menu(menubar, tearoff=0)
        play_menu.add_command(label='Undo', command=self._undo)
        play_menu.add_command(label='Redo', command=self._redo)
        play_menu.add_command(label='Hint', command=self._hint)
        play_menu.add_checkbutton(
            label='Highlight current color',
            variable=self._highlight_current,
            command=self._refresh_highlight,
        )
        play_menu.add_command(label='Toggle preview', command=self._canvas_toggle_preview)
        menubar.add_cascade(label='Play', menu=play_menu)
        self._root.config(menu=menubar)

    def _build_file_controls(self, toolbar: tk.Frame) -> None:
        tk.Button(toolbar, text='Open image…', command=self._open_image).pack(side=tk.LEFT)
        tk.Button(toolbar, text='Open URL…', command=self._open_url).pack(side=tk.LEFT, padx=4)
        tk.Button(toolbar, text='New puzzle', command=self._regenerate).pack(side=tk.LEFT, padx=4)
        tk.Button(toolbar, text='Cancel', command=self._cancel_generate).pack(side=tk.LEFT, padx=4)
        tk.Label(toolbar, text='Preset:').pack(side=tk.LEFT, padx=(12, 2))
        self._preset = ttk.Combobox(
            toolbar,
            values=[preset.name for preset in DifficultyPresets.all()],
            width=8,
            state='readonly',
        )
        self._preset.set(DifficultyPresets.NORMAL.name)
        self._preset.bind('<<ComboboxSelected>>', self._apply_preset)
        self._preset.pack(side=tk.LEFT)
        tk.Label(toolbar, text='Colors:').pack(side=tk.LEFT, padx=(12, 2))
        tk.Spinbox(toolbar, from_=2, to=16, width=4, textvariable=self._n_colors).pack(side=tk.LEFT)

    def _build_play_controls(self, toolbar: tk.Frame) -> None:
        tk.Button(toolbar, text='Undo', command=self._undo).pack(side=tk.LEFT, padx=(12, 2))
        tk.Button(toolbar, text='Redo', command=self._redo).pack(side=tk.LEFT, padx=2)
        tk.Button(toolbar, text='Hint', command=self._hint).pack(side=tk.LEFT, padx=2)
        tk.Button(toolbar, text='Lines −', command=self._canvas_thin_lines).pack(side=tk.LEFT, padx=(12, 2))
        tk.Button(toolbar, text='Lines +', command=self._canvas_thicken_lines).pack(side=tk.LEFT, padx=2)

    def _build_zoom_controls(self, toolbar: tk.Frame) -> None:
        tk.Button(toolbar, text='Zoom −', command=self._canvas.zoom_out).pack(side=tk.RIGHT)
        tk.Button(toolbar, text='Zoom +', command=self._canvas.zoom_in).pack(side=tk.RIGHT, padx=4)
        tk.Button(toolbar, text='100%', command=self._canvas.zoom_100).pack(side=tk.RIGHT, padx=4)
        tk.Button(toolbar, text='Fit', command=self._canvas.reset_zoom).pack(side=tk.RIGHT, padx=4)

    def _bind_shortcuts(self) -> None:
        self._root.bind('<Control-z>', lambda _e: self._undo())
        self._root.bind('<Control-y>', lambda _e: self._redo())
        self._root.bind('<Control-Z>', lambda _e: self._undo())
        self._root.bind('<Control-Y>', lambda _e: self._redo())
        self._root.bind('<Key-h>', lambda _e: self._hint())
        self._root.bind('<Key-plus>', lambda _e: self._canvas.zoom_in())
        self._root.bind('<Key-equal>', lambda _e: self._canvas.zoom_in())
        self._root.bind('<Key-minus>', lambda _e: self._canvas.zoom_out())
        self._root.bind('<Key-0>', lambda _e: self._canvas.reset_zoom())
        self._root.bind('<Key-1>', lambda _e: self._canvas.zoom_100())
        self._root.bind('<Key-p>', lambda _e: self._canvas_toggle_preview())
        self._root.bind('<Left>', lambda _e: self._canvas.pan(PuzzleCanvas._PAN_STEP, 0))
        self._root.bind('<Right>', lambda _e: self._canvas.pan(-PuzzleCanvas._PAN_STEP, 0))
        self._root.bind('<Up>', lambda _e: self._canvas.pan(0, PuzzleCanvas._PAN_STEP))
        self._root.bind('<Down>', lambda _e: self._canvas.pan(0, -PuzzleCanvas._PAN_STEP))

    def _enable_drag_and_drop(self) -> None:
        # Optional: tkinterdnd2 requires a special Tk root and can be unstable on
        # some X11 setups, so we only enable it when a drop hook is already present.
        if not hasattr(self._root, 'drop_target_register'):
            return
        try:
            from tkinterdnd2 import DND_FILES
        except ImportError:
            return
        self._root.drop_target_register(DND_FILES)
        self._root.dnd_bind('<<Drop>>', self._on_drop)

    def _on_drop(self, event) -> None:
        path = str(getattr(event, 'data', '')).strip().strip('{}')
        if path:
            self._load_path(path)

    def _apply_preset(self, _event=None) -> None:
        selected = self._preset.get()
        for preset in DifficultyPresets.all():
            if preset.name == selected:
                self._use_preset(preset)
                return

    def _use_preset(self, preset: DifficultyPreset) -> None:
        self._n_colors.set(preset.n_colors)
        self._min_region_area = preset.min_region_area
        if self._rgb is not None:
            self._regenerate()

    def _open_image(self) -> None:
        path = filedialog.askopenfilename(
            title='Choose a photo',
            filetypes=[
                ('Images', '*.jpg *.jpeg *.png *.bmp *.webp'),
                ('All files', '*.*'),
            ],
        )
        if path:
            self._load_path(path)

    def _load_path(self, path: str) -> None:
        self._source_kind = 'file'
        self._source_value = path
        self._recents.remember('file', path)
        self._start_prepare_job(path=path)

    def _open_url(self) -> None:
        url = simpledialog.askstring(
            'Open URL',
            'Image URL (http:// or https://):',
            parent=self._root,
        )
        if not url:
            return
        self._load_url(url)

    def _load_url(self, url: str) -> None:
        if self._generate_thread and self._generate_thread.is_alive():
            messagebox.showinfo('Color by Numbers', 'Generation already running.')
            return
        self._source_kind = 'url'
        self._source_value = url
        self._recents.remember('url', url)
        self._start_prepare_job(url=url)

    def _open_recent(self) -> None:
        entries = self._recents.list()
        if not entries:
            messagebox.showinfo('Color by Numbers', 'No recent images yet.')
            return
        labels = [f'{item["kind"]}: {item["value"]}' for item in entries]
        choice = simpledialog.askstring(
            'Recent',
            'Enter number:\n' + '\n'.join(f'{i + 1}. {label}' for i, label in enumerate(labels[:10])),
            parent=self._root,
        )
        if not choice or not choice.isdigit():
            return
        index = int(choice) - 1
        if index < 0 or index >= len(entries):
            return
        item = entries[index]
        if item['kind'] == 'file':
            self._load_path(item['value'])
        else:
            self._load_url(item['value'])

    def _regenerate(self) -> None:
        if self._rgb is None:
            messagebox.showinfo('Color by Numbers', 'Open an image or URL first.')
            return
        self._start_prepare_job(rgb=self._rgb)

    def _start_prepare_job(
        self,
        rgb=None,
        url: str | None = None,
        path: str | None = None,
    ) -> None:
        if self._generate_thread and self._generate_thread.is_alive():
            messagebox.showinfo('Color by Numbers', 'Generation already running.')
            return
        self._cancel_event = threading.Event()
        self._job_result = None
        n_colors = int(self._n_colors.get())
        min_area = self._min_region_area
        include_download = url is not None
        tracker = GenerationProgress(include_download=include_download or path is not None)

        download_state = {'bytes': 0, 'total': None, 'started': None}

        def on_progress(
            fraction: float,
            message: str,
            eta_seconds: float | None,
            _elapsed: float,
        ) -> None:
            with self._progress_lock:
                self._latest_progress = {
                    'fraction': fraction,
                    'message': message,
                    'eta': eta_seconds,
                    'work': self._format_work_detail(download_state, message),
                }

        def worker() -> None:
            stop_pulse = threading.Event()

            def pulse_loop() -> None:
                while not stop_pulse.wait(0.15):
                    on_progress(*tracker.pulse())

            pulser = threading.Thread(target=pulse_loop, daemon=True)
            pulser.start()
            try:
                source = rgb
                if url is not None:
                    download_state['started'] = time.perf_counter()

                    def on_download(downloaded: int, total: int | None) -> None:
                        download_state['bytes'] = downloaded
                        download_state['total'] = total
                        on_progress(*tracker.set_download_progress(downloaded, total))

                    on_progress(*tracker.set_download_progress(0, None))
                    source = self._image_loader.load_from_url(url, progress=on_download)
                    on_progress(*tracker.complete_download())
                    on_progress(*tracker.complete_decode())
                    self._rgb = source
                elif path is not None:
                    on_progress(*tracker.set_download_progress(0, 1))
                    source = self._image_loader.load_from_path(path)
                    on_progress(*tracker.set_download_progress(1, 1))
                    on_progress(*tracker.complete_download())
                    on_progress(*tracker.complete_decode())
                    self._rgb = source
                elif source is not None:
                    on_progress(*tracker.complete_decode())
                puzzle = self._generator.generate(
                    source,
                    n_colors=n_colors,
                    min_region_area=min_area,
                    progress=on_progress,
                    cancel_event=self._cancel_event,
                    tracker=tracker,
                )
            except InterruptedError:
                with self._progress_lock:
                    self._job_result = {'status': 'cancelled'}
                return
            except Exception as exc:  # noqa: BLE001 - show any generation failure in UI
                with self._progress_lock:
                    self._job_result = {'status': 'error', 'error': exc}
                return
            finally:
                stop_pulse.set()
            # Hand result to the Tk thread via the loading tick — never call after() here.
            with self._progress_lock:
                self._job_result = {
                    'status': 'ready',
                    'puzzle': puzzle,
                    'tracker': tracker,
                }

        if include_download:
            title = 'Downloading image…'
        elif path is not None:
            title = 'Loading image…'
        else:
            title = 'Generating puzzle…'
        self._latest_progress = {'fraction': 0.0, 'message': title, 'eta': None, 'work': ''}
        self._loading.show(title)
        self._status.set(title)
        self._schedule_loading_tick()
        self._generate_thread = threading.Thread(target=worker, daemon=True)
        self._generate_thread.start()

    def _format_work_detail(self, download_state: dict, message: str) -> str:
        if not message.startswith('Download'):
            return ''
        downloaded = int(download_state.get('bytes') or 0)
        total = download_state.get('total')
        started = download_state.get('started')
        speed = ''
        if started is not None:
            elapsed = max(0.001, time.perf_counter() - float(started))
            speed = f'  ·  {self._format_bytes(downloaded / elapsed)}/s'
        if isinstance(total, int) and total > 0:
            return f'{self._format_bytes(downloaded)} / {self._format_bytes(total)}{speed}'
        if downloaded > 0:
            return f'{self._format_bytes(downloaded)} downloaded{speed}'
        return 'Waiting for first bytes…'

    def _format_bytes(self, size: float) -> str:
        units = ('B', 'KB', 'MB', 'GB')
        value = float(size)
        for unit in units:
            if value < 1024.0 or unit == units[-1]:
                if unit == 'B':
                    return f'{int(value)} {unit}'
                return f'{value:.1f} {unit}'
            value /= 1024.0
        return f'{value:.1f} GB'

    def _schedule_loading_tick(self) -> None:
        if self._loading_tick_scheduled:
            return
        self._loading_tick_scheduled = True
        self._root.after(100, self._on_loading_tick)

    def _on_loading_tick(self) -> None:
        self._loading_tick_scheduled = False
        if not self._loading.visible:
            return
        with self._progress_lock:
            snapshot = dict(self._latest_progress)
            result = self._job_result
            self._job_result = None
        if result is not None:
            self._apply_job_result(result)
            return
        message = str(snapshot['message'])
        fraction = float(snapshot['fraction'] or 0.0)
        eta = snapshot['eta']
        eta_value = float(eta) if isinstance(eta, (int, float)) else None
        work = str(snapshot.get('work') or '')
        self._status.set(message)
        # Elapsed is driven by the overlay clock so the timer always ticks.
        self._loading.set_progress(fraction, message, eta_value, work_detail=work)
        self._schedule_loading_tick()

    def _apply_job_result(self, result: dict) -> None:
        status = result.get('status')
        if status == 'cancelled':
            self._on_generate_cancelled()
            return
        if status == 'error':
            self._on_generate_failed(result['error'])
            return
        tracker = result.get('tracker')
        if isinstance(tracker, GenerationProgress):
            fraction, message, eta, _elapsed = tracker.finish()
            self._loading.set_progress(fraction, message, eta)
            self._root.update_idletasks()
        self._on_puzzle_ready(result['puzzle'])

    def _set_loading_detail(self, message: str) -> None:
        self._status.set(message)
        self._loading.set_detail(message)

    def _on_generate_cancelled(self) -> None:
        self._loading.hide()
        self._status.set('Generation cancelled')

    def _on_generate_failed(self, exc: Exception) -> None:
        self._loading.hide()
        self._status.set('Generation failed')
        messagebox.showerror('Color by Numbers', str(exc))

    def _cancel_generate(self) -> None:
        if self._cancel_event is not None:
            self._cancel_event.set()
            self._set_loading_detail('Cancelling…')

    def _on_puzzle_ready(self, puzzle) -> None:
        self._loading.hide()
        self._puzzle = puzzle
        remaining = {
            index: puzzle.remaining_for_color(index)
            for index in range(len(puzzle.palette))
        }
        self._palette.set_palette(puzzle.palette, remaining)
        self._canvas.show_puzzle(puzzle)
        self._refresh_highlight()
        self._update_status()

    def _on_palette_select(self, index: int) -> None:
        self._refresh_highlight()
        self._update_status()

    def _refresh_highlight(self) -> None:
        if self._puzzle is None:
            return
        color_id = self._palette.selected_index() if self._highlight_current.get() else None
        self._canvas.set_highlight_color(color_id)

    def _on_canvas_click(self, x: int, y: int) -> None:
        if self._puzzle is None:
            return
        selected = self._palette.selected_index()
        region_id = self._puzzle.try_fill(x, y, selected)
        if region_id is None:
            return
        self._sound.fill_success()
        self._canvas.flash_fill()
        self._canvas.set_hint_region(None)
        if self._puzzle.is_complete():
            self._finish_puzzle()
            return
        if self._puzzle.color_is_complete(selected):
            nxt = self._puzzle.next_incomplete_color(selected)
            if nxt is not None:
                self._palette.select(nxt)
        self._sync_palette_remaining()
        self._canvas.redraw()
        self._refresh_highlight()
        self._update_status()

    def _finish_puzzle(self) -> None:
        self._sound.puzzle_complete()
        self._canvas.show_preview(self._puzzle)
        self._status.set('Complete!')
        messagebox.showinfo('Color by Numbers', 'Puzzle complete!')

    def _undo(self) -> None:
        if self._puzzle is None or self._puzzle.undo() is None:
            return
        self._sync_palette_remaining()
        self._canvas.redraw()
        self._refresh_highlight()
        self._update_status()

    def _redo(self) -> None:
        if self._puzzle is None or self._puzzle.redo() is None:
            return
        self._sync_palette_remaining()
        self._canvas.redraw()
        self._refresh_highlight()
        self._update_status()

    def _hint(self) -> None:
        if self._puzzle is None:
            return
        candidates = self._puzzle.unfilled_regions_for_color(self._palette.selected_index())
        if not candidates:
            messagebox.showinfo('Color by Numbers', 'No remaining regions for this color.')
            return
        region_id = candidates[0]
        self._canvas.set_hint_region(region_id)
        self._root.after(900, lambda: self._canvas.set_hint_region(None))

    def _canvas_toggle_preview(self) -> None:
        self._canvas.toggle_preview_overlay()

    def _canvas_thicken_lines(self) -> None:
        self._canvas.thicken_lines()

    def _canvas_thin_lines(self) -> None:
        self._canvas.thin_lines()

    def _sync_palette_remaining(self) -> None:
        if self._puzzle is None:
            return
        remaining = {
            index: self._puzzle.remaining_for_color(index)
            for index in range(len(self._puzzle.palette))
        }
        self._palette.update_remaining(remaining)

    def _save_session(self) -> None:
        if self._puzzle is None:
            messagebox.showinfo('Color by Numbers', 'No puzzle to save.')
            return
        path = filedialog.asksaveasfilename(
            defaultextension='.cbn.npz',
            filetypes=[('Color by Numbers save', '*.cbn.npz')],
        )
        if not path:
            return
        self._sessions.save(path, self._puzzle, int(self._n_colors.get()))
        self._status.set(f'Saved {Path(path).name}')

    def _load_session(self) -> None:
        path = filedialog.askopenfilename(filetypes=[('Color by Numbers save', '*.cbn.npz')])
        if not path:
            return
        puzzle, n_colors = self._sessions.load(path)
        self._puzzle = puzzle
        self._n_colors.set(n_colors)
        self._on_puzzle_ready(puzzle)

    def _export_png(self) -> None:
        if self._puzzle is None:
            return
        path = filedialog.asksaveasfilename(defaultextension='.png', filetypes=[('PNG', '*.png')])
        if path:
            self._exporter.export_png(path, self._puzzle)

    def _export_pdf(self) -> None:
        if self._puzzle is None:
            return
        path = filedialog.asksaveasfilename(defaultextension='.pdf', filetypes=[('PDF', '*.pdf')])
        if path:
            self._exporter.export_pdf(path, self._puzzle)

    def _update_status(self) -> None:
        if self._puzzle is None:
            return
        self._status.set(self._puzzle.status_summary(self._palette.selected_index()))
