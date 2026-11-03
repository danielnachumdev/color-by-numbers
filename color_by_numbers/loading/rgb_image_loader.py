from urllib.parse import urlparse

import cv2
import numpy as np

from .http_gateway import HttpGateway


class RgbImageLoader:
    def __init__(self, http: HttpGateway | None = None) -> None:
        self._http = http or HttpGateway()

    def load_from_path(self, path: str) -> np.ndarray:
        image = cv2.imread(path)
        return self._bgr_to_rgb(image, f'Could not read image: {path}')

    def load_from_url(self, url: str) -> np.ndarray:
        self._require_http_url(url)
        return self.load_from_bytes(self._http.get(url.strip()))

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
        return cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
