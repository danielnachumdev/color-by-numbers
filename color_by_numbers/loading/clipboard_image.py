import numpy as np
from PIL import Image, ImageGrab


class ClipboardImage:
    def grab_rgb(self) -> np.ndarray:
        image = ImageGrab.grabclipboard()
        if image is None:
            raise ValueError('Clipboard does not contain an image')
        if not isinstance(image, Image.Image):
            raise ValueError('Clipboard does not contain an image')
        rgb = image.convert('RGB')
        return np.asarray(rgb, dtype=np.uint8)
