import tkinter as tk
from tkinter import messagebox

from ..difficulty_preset import DifficultyPresets
from .settings_snapshot import SettingsSnapshot


class SettingsWiring:
    def __init__(self, host) -> None:
        self._host = host
        self._snapshot = SettingsSnapshot()

    def apply_initial_geometry(self) -> None:
        host = self._host
        host._root.update_idletasks()
        saved = host._settings.get('geometry')
        if isinstance(saved, str) and saved:
            host._root.geometry(saved)
        else:
            geometry = host._window_geometry.geometry_string(
                host._root.winfo_screenwidth(),
                host._root.winfo_screenheight(),
            )
            host._root.geometry(geometry)
        host._root.minsize(720, 520)

    def apply_saved_ui_state(self) -> None:
        host = self._host
        preset_name = str(host._settings.get('preset', DifficultyPresets.NORMAL.name))
        host._preset.set(preset_name)
        for preset in DifficultyPresets.all():
            if preset.name == preset_name:
                host._use_preset(preset, regenerate=False)
                break
        host._presentation.sync_paint_mode()
        self.apply_language_labels()

    def apply_language_labels(self) -> None:
        host = self._host
        host._root.title(host._strings.t('app_title'))
        if host._strings.rtl:
            try:
                host._root.tk.call('tk', 'scaling', host._root.tk.call('tk', 'scaling'))
            except tk.TclError:
                pass

    def set_language(self, language: str) -> None:
        host = self._host
        host._strings.set_language(language)
        host._settings.set('language', language)
        self.apply_language_labels()
        messagebox.showinfo(
            host._strings.t('app_title'),
            host._strings.t('language') + f': {language}',
        )

    def persist_on_close(self) -> None:
        host = self._host
        host._settings.update(
            self._snapshot.build(
                geometry=host._root.geometry(),
                paint_mode=host._paint_mode.get(),
                highlight=host._highlight_current.get(),
                edge_aware=host._edge_aware.get(),
                color_mode=host._color_mode.get(),
                preset=host._preset.get(),
                n_colors=int(host._n_colors.get()),
                paper=host._paper_size.get(),
                language=host._strings.language,
            )
        )
        host._root.destroy()
