import cv2
import numpy as np


class WebcamCapture:
    def capture_rgb(self, camera_index: int = 0) -> np.ndarray:
        capture = cv2.VideoCapture(camera_index)
        if not capture.isOpened():
            capture.release()
            raise ValueError(f'Could not open camera {camera_index}')
        try:
            ok, frame = capture.read()
        finally:
            capture.release()
        if not ok or frame is None or frame.size == 0:
            raise ValueError('Camera returned an empty frame')
        return cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
