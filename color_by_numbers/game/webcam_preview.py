import tkinter as tk

import cv2
import numpy as np
from PIL import Image, ImageTk


class WebcamPreview:
    def __init__(self, parent: tk.Misc, camera_index: int = 0) -> None:
        self._parent = parent
        self._camera_index = camera_index
        self._capture = None
        self._photo = None
        self._result: np.ndarray | None = None
        self._running = False

    def choose_frame(self) -> np.ndarray | None:
        self._capture = cv2.VideoCapture(self._camera_index)
        if not self._capture.isOpened():
            self._release()
            raise ValueError(f'Could not open camera {self._camera_index}')
        self._result = None
        self._running = True
        dialog = tk.Toplevel(self._parent)
        dialog.title('Webcam')
        dialog.transient(self._parent)
        dialog.grab_set()
        label = tk.Label(dialog)
        label.pack(padx=8, pady=8)
        buttons = tk.Frame(dialog)
        buttons.pack(pady=8)
        tk.Button(buttons, text='Capture', command=lambda: self._capture_frame(dialog)).pack(
            side=tk.LEFT, padx=4
        )
        tk.Button(buttons, text='Cancel', command=lambda: self._cancel(dialog)).pack(side=tk.LEFT, padx=4)
        self._tick(label, dialog)
        dialog.wait_window()
        self._release()
        return self._result

    def _tick(self, label: tk.Label, dialog: tk.Toplevel) -> None:
        if not self._running or self._capture is None:
            return
        ok, frame = self._capture.read()
        if ok and frame is not None:
            rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            preview = Image.fromarray(rgb)
            preview.thumbnail((640, 480))
            self._photo = ImageTk.PhotoImage(preview)
            label.configure(image=self._photo)
            self._latest = rgb
        dialog.after(33, lambda: self._tick(label, dialog))

    def _capture_frame(self, dialog: tk.Toplevel) -> None:
        self._result = getattr(self, '_latest', None)
        self._running = False
        dialog.destroy()

    def _cancel(self, dialog: tk.Toplevel) -> None:
        self._result = None
        self._running = False
        dialog.destroy()

    def _release(self) -> None:
        self._running = False
        if self._capture is not None:
            self._capture.release()
            self._capture = None
