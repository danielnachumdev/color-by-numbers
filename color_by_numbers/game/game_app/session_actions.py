from pathlib import Path
from tkinter import filedialog, messagebox, simpledialog


class SessionActions:
    def __init__(self, host) -> None:
        self._host = host

    def save_session(self) -> None:
        host = self._host
        if host._puzzle is None:
            messagebox.showinfo('Color by Numbers', 'No puzzle to save.')
            return
        path = filedialog.asksaveasfilename(
            defaultextension='.cbn.npz',
            filetypes=[('Color by Numbers save', '*.cbn.npz')],
        )
        if not path:
            return
        host._sessions.save(path, host._puzzle, int(host._n_colors.get()))
        host._status.set(f'Saved {Path(path).name}')

    def load_session(self) -> None:
        host = self._host
        path = filedialog.askopenfilename(filetypes=[('Color by Numbers save', '*.cbn.npz')])
        if not path:
            return
        puzzle, n_colors = host._sessions.load(path)
        host._n_colors.set(n_colors)
        host._presentation.show_puzzle(puzzle)

    def autosave_slot_dialog(self) -> None:
        host = self._host
        if host._puzzle is None:
            messagebox.showinfo('Color by Numbers', 'No puzzle to autosave.')
            return
        choice = simpledialog.askstring('Autosave', 'Slot number (1-3):', parent=host._root)
        if not choice or not choice.isdigit():
            return
        path = host._autosave.save_slot(
            int(choice),
            host._puzzle,
            int(host._n_colors.get()),
            label=str(host._source_value or ''),
        )
        host._status.set(f'Autosaved {path.name}')

    def load_autosave_slot_dialog(self) -> None:
        host = self._host
        slots = host._autosave.list_slots()
        lines = [
            f'{item["slot"]}. {"empty" if not item["exists"] else item["label"] or "saved"}'
            for item in slots
        ]
        choice = simpledialog.askstring(
            'Load autosave',
            'Slot number:\n' + '\n'.join(lines),
            parent=host._root,
        )
        if not choice or not choice.isdigit():
            return
        loaded = host._autosave.load_slot(int(choice))
        if loaded is None:
            messagebox.showinfo('Color by Numbers', 'That autosave slot is empty.')
            return
        puzzle, n_colors = loaded
        host._n_colors.set(n_colors)
        host._presentation.show_puzzle(puzzle)

    def offer_resume_last(self) -> None:
        host = self._host
        loaded = host._autosave.load_last()
        if loaded is None:
            return
        puzzle, n_colors, slot = loaded
        if not messagebox.askyesno(
            host._strings.t('app_title'),
            host._strings.t('resume_autosave', slot=slot),
        ):
            return
        host._n_colors.set(n_colors)
        host._presentation.show_puzzle(puzzle)

    def schedule_autosave(self) -> None:
        host = self._host
        if host._autosave_after is not None:
            host._root.after_cancel(host._autosave_after)
        host._autosave_after = host._root.after(1200, self.autosave_now)

    def autosave_now(self) -> None:
        host = self._host
        host._autosave_after = None
        if host._puzzle is None:
            return
        host._autosave.save_slot(
            1,
            host._puzzle,
            int(host._n_colors.get()),
            label=str(host._source_value or 'autosave'),
        )
