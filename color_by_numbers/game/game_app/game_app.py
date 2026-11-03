import tkinter as tk

import numpy as np

from ...i18n import UiStrings
from ...loading.clipboard_image import ClipboardImage
from ...loading.rgb_image_loader import RgbImageLoader
from ...loading.webcam_capture import WebcamCapture
from ...persistence.app_settings import AppSettings
from ...persistence.autosave_store import AutosaveStore
from ...persistence.puzzle_session import PuzzleSession
from ...persistence.recent_sources import RecentSources
from ...puzzle.puzzle_generator import PuzzleGenerator
from ..color_blind_palette import ColorBlindPalette
from ..difficulty_preset import DifficultyPreset, DifficultyPresets
from ..feedback_sound import FeedbackSound
from ..loading_overlay import LoadingOverlay
from ..palette_panel import PalettePanel
from ..play_timer import PlayTimer
from ..puzzle_canvas import PuzzleCanvas
from ..screen_window_geometry import ScreenWindowGeometry
from ..sheet_exporter import SheetExporter
from .drag_drop import DragDropBinder
from .export_replay_actions import ExportReplayActions
from .loading_job_controller import LoadingJobController
from .menu_builder import MenuBuilder
from .play_actions import PlayActions
from .prepare_generate_job import PrepareGenerateJob
from .puzzle_presentation import PuzzlePresentation
from .session_actions import SessionActions
from .settings_wiring import SettingsWiring
from .source_actions import SourceActions
from .toolbar_builder import ToolbarBuilder


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
        self._loading_tick_scheduled = False
        self._autosave_after: str | None = None
        self._root = tk.Tk()
        self._paper_size = tk.StringVar(value=str(self._settings.get('paper', 'A4')))
        self._n_colors = tk.IntVar(value=int(self._settings.get('n_colors', 8)))
        self._status = tk.StringVar(value='Open an image or URL to start')
        self._highlight_current = tk.BooleanVar(value=bool(self._settings.get('highlight', True)))
        self._paint_mode = tk.BooleanVar(value=bool(self._settings.get('paint_mode', False)))
        self._edge_aware = tk.BooleanVar(value=bool(self._settings.get('edge_aware', True)))
        self._lock_palette = tk.BooleanVar(value=False)
        self._color_mode = tk.StringVar(value=str(self._settings.get('color_mode', 'Normal')))
        self._sound = FeedbackSound(self._root)
        self._prepare_job = PrepareGenerateJob(
            image_loader=self._image_loader,
            generator=self._generator,
        )
        self._settings_ui = SettingsWiring(self)
        self._sources = SourceActions(self)
        self._sessions_ui = SessionActions(self)
        self._exports = ExportReplayActions(self)
        self._play = PlayActions(self)
        self._loading_job = LoadingJobController(self)
        self._presentation = PuzzlePresentation(self)
        self._settings_ui.apply_initial_geometry()
        self._build_layout()
        self._bind_shortcuts()
        DragDropBinder().enable(self._root, self._on_drop)
        self._settings_ui.apply_saved_ui_state()
        self._root.protocol('WM_DELETE_WINDOW', self._settings_ui.persist_on_close)
        self._root.after(200, self._sessions_ui.offer_resume_last)

    def run(self) -> None:
        self._root.mainloop()

    def _build_layout(self) -> None:
        MenuBuilder(self).build()
        toolbar = tk.Frame(self._root)
        toolbar.pack(fill=tk.X, padx=8, pady=4)
        tools = ToolbarBuilder(self)
        tools.build_file_controls(toolbar)
        tools.build_play_controls(toolbar)
        tk.Label(self._root, textvariable=self._status).pack(fill=tk.X, padx=8)
        self._canvas = PuzzleCanvas(self._root, on_click=self._play.on_canvas_click)
        self._canvas.pack(fill=tk.BOTH, expand=True, padx=8, pady=8)
        self._loading = LoadingOverlay(self._root)
        tools.build_zoom_controls(toolbar)
        self._palette = PalettePanel(
            self._root,
            on_select=self._presentation.on_palette_select,
        )
        self._palette.pack(fill=tk.X, padx=8, pady=8)

    def _bind_shortcuts(self) -> None:
        self._root.bind('<Control-z>', lambda _e: self._play.undo())
        self._root.bind('<Control-y>', lambda _e: self._play.redo())
        self._root.bind('<Control-Z>', lambda _e: self._play.undo())
        self._root.bind('<Control-Y>', lambda _e: self._play.redo())
        self._root.bind('<Control-v>', lambda _e: self._sources.paste_clipboard())
        self._root.bind('<Control-V>', lambda _e: self._sources.paste_clipboard())
        self._root.bind('<Key-h>', lambda _e: self._play.hint())
        self._root.bind('<Key-plus>', lambda _e: self._canvas.zoom_in())
        self._root.bind('<Key-equal>', lambda _e: self._canvas.zoom_in())
        self._root.bind('<Key-minus>', lambda _e: self._canvas.zoom_out())
        self._root.bind('<Key-0>', lambda _e: self._canvas.reset_zoom())
        self._root.bind('<Key-1>', lambda _e: self._canvas.zoom_100())
        self._root.bind('<Key-p>', lambda _e: self._canvas.toggle_preview_overlay())
        self._root.bind('<Left>', lambda _e: self._canvas.pan(PuzzleCanvas._PAN_STEP, 0))
        self._root.bind('<Right>', lambda _e: self._canvas.pan(-PuzzleCanvas._PAN_STEP, 0))
        self._root.bind('<Up>', lambda _e: self._canvas.pan(0, PuzzleCanvas._PAN_STEP))
        self._root.bind('<Down>', lambda _e: self._canvas.pan(0, -PuzzleCanvas._PAN_STEP))

    def _on_drop(self, event) -> None:
        path = str(getattr(event, 'data', '')).strip().strip('{}')
        if path:
            self._sources.load_path(path)

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
            self._sources.regenerate()

    def _set_rgb(self, rgb) -> None:
        self._rgb = rgb
