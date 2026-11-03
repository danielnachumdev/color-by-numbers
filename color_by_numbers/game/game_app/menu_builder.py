import tkinter as tk

from ..color_blind_palette import ColorBlindPalette


class MenuBuilder:
    def __init__(self, host) -> None:
        self._host = host

    def build(self) -> None:
        host = self._host
        menubar = tk.Menu(host._root)
        menubar.add_cascade(label='File', menu=self._file_menu(menubar))
        menubar.add_cascade(label='Play', menu=self._play_menu(menubar))
        menubar.add_cascade(label='Vision', menu=self._vision_menu(menubar))
        menubar.add_cascade(label='Settings', menu=self._settings_menu(menubar))
        host._root.config(menu=menubar)

    def _file_menu(self, menubar: tk.Menu) -> tk.Menu:
        host = self._host
        menu = tk.Menu(menubar, tearoff=0)
        menu.add_command(label='Open image…', command=host._sources.open_image)
        menu.add_command(label='Open URL…', command=host._sources.open_url)
        menu.add_command(label='Paste image', command=host._sources.paste_clipboard)
        menu.add_command(label='Capture webcam…', command=host._sources.capture_webcam)
        menu.add_command(label='Open gallery folder…', command=host._sources.open_gallery_folder)
        menu.add_command(label='Recent…', command=host._sources.open_recent)
        menu.add_separator()
        menu.add_command(label='Save progress…', command=host._sessions_ui.save_session)
        menu.add_command(label='Load progress…', command=host._sessions_ui.load_session)
        menu.add_command(label='Autosave slot…', command=host._sessions_ui.autosave_slot_dialog)
        menu.add_command(
            label='Load autosave slot…',
            command=host._sessions_ui.load_autosave_slot_dialog,
        )
        menu.add_command(label='Export PNG…', command=host._exports.export_png)
        menu.add_command(label='Export PDF…', command=host._exports.export_pdf)
        menu.add_command(label='Export completed sheet…', command=host._exports.export_completed)
        menu.add_command(label='Replay fills', command=host._exports.replay_fills)
        return menu

    def _play_menu(self, menubar: tk.Menu) -> tk.Menu:
        host = self._host
        menu = tk.Menu(menubar, tearoff=0)
        menu.add_command(label='Undo', command=host._play.undo)
        menu.add_command(label='Redo', command=host._play.redo)
        menu.add_command(label='Hint', command=host._play.hint)
        menu.add_checkbutton(
            label='Highlight current color',
            variable=host._highlight_current,
            command=host._presentation.refresh_highlight,
        )
        menu.add_checkbutton(
            label='Paint mode (drag fill)',
            variable=host._paint_mode,
            command=host._presentation.sync_paint_mode,
        )
        menu.add_checkbutton(
            label='Edge-aware colors',
            variable=host._edge_aware,
        )
        menu.add_checkbutton(
            label='Lock current palette',
            variable=host._lock_palette,
            command=host._presentation.toggle_palette_lock,
        )
        menu.add_command(
            label='Toggle preview',
            command=lambda: host._canvas.toggle_preview_overlay(),
        )
        return menu

    def _vision_menu(self, menubar: tk.Menu) -> tk.Menu:
        host = self._host
        menu = tk.Menu(menubar, tearoff=0)
        for mode in ColorBlindPalette.MODES:
            menu.add_radiobutton(
                label=mode,
                variable=host._color_mode,
                value=mode,
                command=host._presentation.apply_color_mode,
            )
        return menu

    def _settings_menu(self, menubar: tk.Menu) -> tk.Menu:
        host = self._host
        menu = tk.Menu(menubar, tearoff=0)
        menu.add_radiobutton(
            label='English',
            command=lambda: host._settings_ui.set_language('en'),
        )
        menu.add_radiobutton(
            label='עברית',
            command=lambda: host._settings_ui.set_language('he'),
        )
        menu.add_separator()
        menu.add_radiobutton(label='Paper A4', variable=host._paper_size, value='A4')
        menu.add_radiobutton(label='Paper Letter', variable=host._paper_size, value='Letter')
        return menu
