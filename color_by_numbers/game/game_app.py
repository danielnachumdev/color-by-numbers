import threading
import time
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox, simpledialog
from tkinter import ttk

import numpy as np

from ..i18n import UiStrings
from ..loading.clipboard_image import ClipboardImage
from ..loading.rgb_image_loader import RgbImageLoader
from ..loading.webcam_capture import WebcamCapture
from ..persistence.app_settings import AppSettings
from ..persistence.autosave_store import AutosaveStore
from ..persistence.puzzle_session import PuzzleSession
from ..persistence.recent_sources import RecentSources
from ..puzzle.generation_progress import GenerationProgress
from ..puzzle.puzzle_generator import PuzzleGenerator
from .color_blind_palette import ColorBlindPalette
from .difficulty_preset import DifficultyPreset, DifficultyPresets
from .feedback_sound import FeedbackSound
from .loading_overlay import LoadingOverlay
from .palette_panel import PalettePanel
from .play_timer import PlayTimer
from .puzzle_canvas import PuzzleCanvas
from .screen_window_geometry import ScreenWindowGeometry
from .sheet_exporter import SheetExporter
from .webcam_preview import WebcamPreview


class GameApp:
    def __init__(
        self,
        generator: PuzzleGenerator | None = None,
        image_loader: RgbImageLoader | None = None,
        window_geometry: ScreenWindowGeometry | None = None,
        recent_sources: RecentSources | None = None,
        session_store: PuzzleSession | None = None,
        exporter: SheetExporter | None = None,
        autosave: AutosaveStore | None = None,
        clipboard: ClipboardImage | None = None,
        webcam: WebcamCapture | None = None,
    ) -> None:
        self._generator = generator or PuzzleGenerator()
        self._image_loader = image_loader or RgbImageLoader()
        self._window_geometry = window_geometry or ScreenWindowGeometry()
        self._recents = recent_sources or RecentSources()
        self._sessions = session_store or PuzzleSession()
        self._exporter = exporter or SheetExporter()
        self._autosave = autosave or AutosaveStore(sessions=self._sessions)
        self._clipboard = clipboard or ClipboardImage()
        self._webcam = webcam or WebcamCapture()
        self._settings = AppSettings()
        self._strings = UiStrings(self._settings.get('language', 'en'))
        self._color_blind = ColorBlindPalette()
        self._timer = PlayTimer()
        self._puzzle = None
        self._rgb = None
        self._source_kind = None
        self._source_value = None
        self._min_region_area: int | None = None
        self._preserve_detail = False
        self._kids_mode = False
        self._max_regions: int | None = None
        self._skin_bias = True
        self._locked_palette: np.ndarray | None = None
        self._paper_size = tk.StringVar(value=str(self._settings.get('paper', 'A4')))
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
        self._autosave_after: str | None = None
        self._root = tk.Tk()
        self._n_colors = tk.IntVar(value=int(self._settings.get('n_colors', 8)))
        self._status = tk.StringVar(value='Open an image or URL to start')
        self._highlight_current = tk.BooleanVar(value=bool(self._settings.get('highlight', True)))
        self._paint_mode = tk.BooleanVar(value=bool(self._settings.get('paint_mode', False)))
        self._edge_aware = tk.BooleanVar(value=bool(self._settings.get('edge_aware', True)))
        self._lock_palette = tk.BooleanVar(value=False)
        self._color_mode = tk.StringVar(value=str(self._settings.get('color_mode', 'Normal')))
        self._sound = FeedbackSound(self._root)
        self._apply_initial_geometry()
        self._build_layout()
        self._bind_shortcuts()
        self._enable_drag_and_drop()
        self._apply_saved_ui_state()
        self._root.protocol('WM_DELETE_WINDOW', self._on_close)
        self._root.after(200, self._offer_resume_last)

    def run(self) -> None:
        self._root.mainloop()

    def _apply_initial_geometry(self) -> None:
        self._root.update_idletasks()
        saved = self._settings.get('geometry')
        if isinstance(saved, str) and saved:
            self._root.geometry(saved)
        else:
            geometry = self._window_geometry.geometry_string(
                self._root.winfo_screenwidth(),
                self._root.winfo_screenheight(),
            )
            self._root.geometry(geometry)
        self._root.minsize(720, 520)

    def _apply_saved_ui_state(self) -> None:
        preset_name = str(self._settings.get('preset', DifficultyPresets.NORMAL.name))
        self._preset.set(preset_name)
        for preset in DifficultyPresets.all():
            if preset.name == preset_name:
                self._use_preset(preset, regenerate=False)
                break
        self._sync_paint_mode()
        self._apply_language_labels()

    def _apply_language_labels(self) -> None:
        self._root.title(self._strings.t('app_title'))
        if self._strings.rtl:
            try:
                self._root.tk.call('tk', 'scaling', self._root.tk.call('tk', 'scaling'))
            except tk.TclError:
                pass

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
        file_menu.add_command(label='Paste image', command=self._paste_clipboard)
        file_menu.add_command(label='Capture webcam…', command=self._capture_webcam)
        file_menu.add_command(label='Open gallery folder…', command=self._open_gallery_folder)
        file_menu.add_command(label='Recent…', command=self._open_recent)
        file_menu.add_separator()
        file_menu.add_command(label='Save progress…', command=self._save_session)
        file_menu.add_command(label='Load progress…', command=self._load_session)
        file_menu.add_command(label='Autosave slot…', command=self._autosave_slot_dialog)
        file_menu.add_command(label='Load autosave slot…', command=self._load_autosave_slot_dialog)
        file_menu.add_command(label='Export PNG…', command=self._export_png)
        file_menu.add_command(label='Export PDF…', command=self._export_pdf)
        file_menu.add_command(label='Export completed sheet…', command=self._export_completed)
        file_menu.add_command(label='Replay fills', command=self._replay_fills)
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
        play_menu.add_checkbutton(
            label='Paint mode (drag fill)',
            variable=self._paint_mode,
            command=self._sync_paint_mode,
        )
        play_menu.add_checkbutton(
            label='Edge-aware colors',
            variable=self._edge_aware,
        )
        play_menu.add_checkbutton(
            label='Lock current palette',
            variable=self._lock_palette,
            command=self._toggle_palette_lock,
        )
        play_menu.add_command(label='Toggle preview', command=self._canvas_toggle_preview)
        menubar.add_cascade(label='Play', menu=play_menu)
        view_menu = tk.Menu(menubar, tearoff=0)
        for mode in ColorBlindPalette.MODES:
            view_menu.add_radiobutton(
                label=mode,
                variable=self._color_mode,
                value=mode,
                command=self._apply_color_mode,
            )
        menubar.add_cascade(label='Vision', menu=view_menu)
        settings_menu = tk.Menu(menubar, tearoff=0)
        settings_menu.add_radiobutton(
            label='English',
            command=lambda: self._set_language('en'),
        )
        settings_menu.add_radiobutton(
            label='עברית',
            command=lambda: self._set_language('he'),
        )
        settings_menu.add_separator()
        settings_menu.add_radiobutton(label='Paper A4', variable=self._paper_size, value='A4')
        settings_menu.add_radiobutton(label='Paper Letter', variable=self._paper_size, value='Letter')
        menubar.add_cascade(label='Settings', menu=settings_menu)
        self._root.config(menu=menubar)

    def _build_file_controls(self, toolbar: tk.Frame) -> None:
        tk.Button(toolbar, text='Open image…', command=self._open_image).pack(side=tk.LEFT)
        tk.Button(toolbar, text='Open URL…', command=self._open_url).pack(side=tk.LEFT, padx=4)
        tk.Button(toolbar, text='Paste', command=self._paste_clipboard).pack(side=tk.LEFT, padx=4)
        tk.Button(toolbar, text='Webcam', command=self._capture_webcam).pack(side=tk.LEFT, padx=4)
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
        self._root.bind('<Control-v>', lambda _e: self._paste_clipboard())
        self._root.bind('<Control-V>', lambda _e: self._paste_clipboard())
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

    def _use_preset(self, preset: DifficultyPreset, regenerate: bool = True) -> None:
        self._n_colors.set(preset.n_colors)
        self._min_region_area = preset.min_region_area
        self._preserve_detail = preset.preserve_detail
        self._kids_mode = preset.kids_mode
        self._max_regions = preset.max_regions
        self._skin_bias = preset.skin_bias
        self._canvas.set_number_scale(1.6 if preset.kids_mode else 1.0)
        self._settings.update({'preset': preset.name, 'n_colors': preset.n_colors})
        if regenerate and self._rgb is not None:
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

    def _open_gallery_folder(self) -> None:
        folder = filedialog.askdirectory(title='Choose a photo folder')
        if not folder:
            return
        paths = sorted(
            [
                str(path)
                for path in Path(folder).iterdir()
                if path.suffix.lower() in {'.jpg', '.jpeg', '.png', '.bmp', '.webp'}
            ]
        )
        if not paths:
            messagebox.showinfo('Color by Numbers', 'No images found in that folder.')
            return
        labels = [Path(path).name for path in paths[:30]]
        choice = simpledialog.askstring(
            'Gallery',
            'Enter number:\n' + '\n'.join(f'{i + 1}. {label}' for i, label in enumerate(labels)),
            parent=self._root,
        )
        if not choice or not choice.isdigit():
            return
        index = int(choice) - 1
        if 0 <= index < len(paths):
            self._load_path(paths[index])

    def _paste_clipboard(self) -> None:
        try:
            rgb = self._clipboard.grab_rgb()
        except ValueError as exc:
            messagebox.showerror('Color by Numbers', str(exc))
            return
        self._source_kind = 'clipboard'
        self._source_value = 'clipboard'
        self._rgb = rgb
        self._start_prepare_job(rgb=rgb)

    def _capture_webcam(self) -> None:
        try:
            rgb = WebcamPreview(self._root).choose_frame()
        except ValueError as exc:
            messagebox.showerror(self._strings.t('app_title'), str(exc))
            return
        if rgb is None:
            return
        self._source_kind = 'webcam'
        self._source_value = 'webcam'
        self._rgb = rgb
        self._start_prepare_job(rgb=rgb)

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
        preserve_detail = self._preserve_detail
        edge_aware = self._edge_aware.get()
        max_regions = self._max_regions
        skin_bias = self._skin_bias
        locked = self._locked_palette if self._lock_palette.get() else None
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
                    n_colors=n_colors if locked is None else len(locked),
                    min_region_area=min_area,
                    progress=on_progress,
                    cancel_event=self._cancel_event,
                    tracker=tracker,
                    edge_aware=edge_aware,
                    preserve_detail=preserve_detail,
                    skin_bias=skin_bias,
                    locked_palette=locked,
                    max_regions=max_regions,
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
        self._timer.reset()
        self._timer.start()
        self._canvas.set_number_scale(1.6 if self._kids_mode else 1.0)
        remaining = {
            index: puzzle.remaining_for_color(index)
            for index in range(len(puzzle.palette))
        }
        display = self._color_blind.remap(puzzle.palette, self._color_mode.get())
        self._palette.set_palette(display, remaining)
        self._canvas.set_display_palette(display)
        self._canvas.show_puzzle(puzzle)
        self._refresh_highlight()
        self._sync_paint_mode()
        self._update_status()
        self._schedule_autosave()

    def _on_palette_select(self, index: int) -> None:
        self._refresh_highlight()
        self._update_status()

    def _refresh_highlight(self) -> None:
        if self._puzzle is None:
            return
        color_id = self._palette.selected_index() if self._highlight_current.get() else None
        self._canvas.set_highlight_color(color_id)

    def _sync_paint_mode(self) -> None:
        enabled = self._paint_mode.get()
        self._canvas.set_paint_mode(enabled)
        self._settings.set('paint_mode', enabled)

    def _set_language(self, language: str) -> None:
        self._strings.set_language(language)
        self._settings.set('language', language)
        self._apply_language_labels()
        messagebox.showinfo(self._strings.t('app_title'), self._strings.t('language') + f': {language}')

    def _toggle_palette_lock(self) -> None:
        if self._lock_palette.get():
            if self._puzzle is None:
                self._lock_palette.set(False)
                messagebox.showinfo('Color by Numbers', 'Generate a puzzle before locking its palette.')
                return
            self._locked_palette = self._puzzle.palette.copy()
            self._status.set('Palette locked for next generate')
        else:
            self._locked_palette = None

    def _apply_color_mode(self) -> None:
        self._settings.set('color_mode', self._color_mode.get())
        if self._puzzle is None:
            return
        display = self._color_blind.remap(self._puzzle.palette, self._color_mode.get())
        remaining = {
            index: self._puzzle.remaining_for_color(index)
            for index in range(len(self._puzzle.palette))
        }
        selected = self._palette.selected_index()
        self._palette.set_palette(display, remaining)
        self._palette.select(selected, notify=False)
        self._canvas.set_display_palette(display)
        self._refresh_highlight()

    def _on_canvas_click(self, x: int, y: int) -> None:
        if self._puzzle is None:
            return
        selected = self._palette.selected_index()
        region_id = self._puzzle.try_fill(x, y, selected)
        if region_id is None:
            return
        self._timer.record_fill()
        self._sound.fill_success()
        if not self._paint_mode.get():
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
        self._schedule_autosave()

    def _finish_puzzle(self) -> None:
        self._timer.stop()
        self._sound.puzzle_complete()
        self._canvas.show_preview(self._puzzle)
        summary = self._timer.summary(len(self._puzzle.region_color_id))
        self._status.set(f'{self._strings.t("complete")}  {summary}')
        messagebox.showinfo(self._strings.t('app_title'), f'{self._strings.t("complete")}\n{summary}')

    def _undo(self) -> None:
        if self._puzzle is None or self._puzzle.undo() is None:
            return
        self._sync_palette_remaining()
        self._canvas.redraw()
        self._refresh_highlight()
        self._update_status()
        self._schedule_autosave()

    def _redo(self) -> None:
        if self._puzzle is None or self._puzzle.redo() is None:
            return
        self._sync_palette_remaining()
        self._canvas.redraw()
        self._refresh_highlight()
        self._update_status()
        self._schedule_autosave()

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
        self._n_colors.set(n_colors)
        self._on_puzzle_ready(puzzle)

    def _autosave_slot_dialog(self) -> None:
        if self._puzzle is None:
            messagebox.showinfo('Color by Numbers', 'No puzzle to autosave.')
            return
        choice = simpledialog.askstring('Autosave', 'Slot number (1-3):', parent=self._root)
        if not choice or not choice.isdigit():
            return
        path = self._autosave.save_slot(
            int(choice),
            self._puzzle,
            int(self._n_colors.get()),
            label=str(self._source_value or ''),
        )
        self._status.set(f'Autosaved {path.name}')

    def _load_autosave_slot_dialog(self) -> None:
        slots = self._autosave.list_slots()
        lines = [
            f'{item["slot"]}. {"empty" if not item["exists"] else item["label"] or "saved"}'
            for item in slots
        ]
        choice = simpledialog.askstring(
            'Load autosave',
            'Slot number:\n' + '\n'.join(lines),
            parent=self._root,
        )
        if not choice or not choice.isdigit():
            return
        loaded = self._autosave.load_slot(int(choice))
        if loaded is None:
            messagebox.showinfo('Color by Numbers', 'That autosave slot is empty.')
            return
        puzzle, n_colors = loaded
        self._n_colors.set(n_colors)
        self._on_puzzle_ready(puzzle)

    def _offer_resume_last(self) -> None:
        loaded = self._autosave.load_last()
        if loaded is None:
            return
        puzzle, n_colors, slot = loaded
        if not messagebox.askyesno(
            self._strings.t('app_title'),
            self._strings.t('resume_autosave', slot=slot),
        ):
            return
        self._n_colors.set(n_colors)
        self._on_puzzle_ready(puzzle)

    def _schedule_autosave(self) -> None:
        if self._autosave_after is not None:
            self._root.after_cancel(self._autosave_after)
        self._autosave_after = self._root.after(1200, self._autosave_now)

    def _autosave_now(self) -> None:
        self._autosave_after = None
        if self._puzzle is None:
            return
        self._autosave.save_slot(
            1,
            self._puzzle,
            int(self._n_colors.get()),
            label=str(self._source_value or 'autosave'),
        )

    def _export_png(self) -> None:
        if self._puzzle is None:
            return
        path = filedialog.asksaveasfilename(defaultextension='.png', filetypes=[('PNG', '*.png')])
        if path:
            self._exporter.export_png(
                path,
                self._puzzle,
                print_ready=True,
                paper=self._paper_size.get(),
            )
            self._settings.set('paper', self._paper_size.get())

    def _export_pdf(self) -> None:
        if self._puzzle is None:
            return
        path = filedialog.asksaveasfilename(defaultextension='.pdf', filetypes=[('PDF', '*.pdf')])
        if path:
            self._exporter.export_pdf(
                path,
                self._puzzle,
                print_ready=True,
                paper=self._paper_size.get(),
                palette_on_second_page=True,
            )
            self._settings.set('paper', self._paper_size.get())

    def _export_completed(self) -> None:
        if self._puzzle is None:
            return
        path = filedialog.asksaveasfilename(defaultextension='.png', filetypes=[('PNG', '*.png')])
        if path:
            self._exporter.export_completed_png(path, self._puzzle)

    def _replay_fills(self) -> None:
        if self._puzzle is None or not self._puzzle.fill_history:
            messagebox.showinfo(self._strings.t('app_title'), 'No fill history to replay.')
            return
        frames = self._puzzle.replay_frames()
        original = set(self._puzzle.filled_regions)
        self._puzzle.filled_regions = set()
        self._canvas.redraw()

        def step(index: int) -> None:
            if index >= len(frames):
                self._puzzle.filled_regions = original
                self._canvas.redraw()
                self._sync_palette_remaining()
                self._update_status()
                return
            self._puzzle.filled_regions = set(frames[index])
            self._canvas.redraw()
            self._root.after(120, lambda: step(index + 1))

        step(0)

    def _on_close(self) -> None:
        self._settings.update(
            {
                'geometry': self._root.geometry(),
                'paint_mode': self._paint_mode.get(),
                'highlight': self._highlight_current.get(),
                'edge_aware': self._edge_aware.get(),
                'color_mode': self._color_mode.get(),
                'preset': self._preset.get(),
                'n_colors': int(self._n_colors.get()),
                'paper': self._paper_size.get(),
                'language': self._strings.language,
            }
        )
        self._root.destroy()

    def _update_status(self) -> None:
        if self._puzzle is None:
            return
        base = self._puzzle.status_summary(self._palette.selected_index())
        timer = self._timer.summary(len(self._puzzle.region_color_id))
        history = len(self._puzzle.fill_history)
        self._status.set(f'{base}  ·  {timer}  ·  fills {history}')
