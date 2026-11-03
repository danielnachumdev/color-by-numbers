from collections.abc import Callable
from urllib.parse import urlparse

import cv2
import numpy as np

from .http_gateway import HttpGateway

DownloadProgress = Callable[[int, int | None], None]


class RgbImageLoader:
    def __init__(self, http: HttpGateway | None = None, max_decode_side: int = 1600) -> None:
        self._http = http or HttpGateway()
        self._max_decode_side = max_decode_side

    def load_from_path(self, path: str) -> np.ndarray:
        image = cv2.imread(path)
        return self._bgr_to_rgb(image, f'Could not read image: {path}')

    def load_from_url(self, url: str, progress: DownloadProgress | None = None) -> np.ndarray:
        self._require_http_url(url)
        return self.load_from_bytes(self._http.get(url.strip(), progress=progress))

    def load_from_bytes(self, data: bytes) -> np.ndarray:
        if not data:
            raise ValueError('Image data is empty')
        buffer = np.frombuffer(data, dtype=np.uint8)
        image = cv2.imdecode(buffer, cv2.IMREAD_COLOR)
        return self._bgr_to_rgb(image, 'Could not decode image data')

    def _require_http_url(self, url: str) -> None:
        parsed = urlparse(url.strip())
        if parsed.scheme not in {'http', 'https'} or not parsed.netloc:
            raise ValueError('URL must start with http:// or https://')

    def _bgr_to_rgb(self, image: np.ndarray | None, error_message: str) -> np.ndarray:
        if image is None or image.size == 0:
            raise ValueError(error_message)
        rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        return self._downscale(rgb)

    def _downscale(self, rgb: np.ndarray) -> np.ndarray:
        height, width = rgb.shape[:2]
        longest = max(height, width)
        if longest <= self._max_decode_side:
            return rgb
        scale = self._max_decode_side / float(longest)
        size = (int(round(width * scale)), int(round(height * scale)))
        return cv2.resize(rgb, size, interpolation=cv2.INTER_AREA)
