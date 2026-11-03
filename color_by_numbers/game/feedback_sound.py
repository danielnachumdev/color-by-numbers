import tkinter as tk


class FeedbackSound:
    def __init__(self, root: tk.Misc) -> None:
        self._root = root

    def fill_success(self) -> None:
        self._root.bell()

    def puzzle_complete(self) -> None:
        self._root.bell()
        self._root.after(120, self._root.bell)
