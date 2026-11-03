import colorsys

import numpy as np


class ColorBlindPalette:
    """Display-only remaps that keep region numbers stable."""

    MODES = ('Normal', 'Deuteranopia', 'Protanopia', 'Tritanopia', 'High contrast')

    _OKABE_ITO = np.array(
        [
            [230, 159, 0],
            [86, 180, 233],
            [0, 158, 115],
            [240, 228, 66],
            [0, 114, 178],
            [213, 94, 0],
            [204, 121, 167],
            [0, 0, 0],
        ],
        dtype=np.uint8,
    )

    def remap(self, palette: np.ndarray, mode: str) -> np.ndarray:
        if mode == 'Normal' or len(palette) == 0:
            return palette.copy()
        if mode == 'High contrast':
            return self._high_contrast(palette)
        return self._cycle_okabe(palette)

    def _cycle_okabe(self, palette: np.ndarray) -> np.ndarray:
        remapped = np.zeros_like(palette)
        for index in range(len(palette)):
            remapped[index] = self._OKABE_ITO[index % len(self._OKABE_ITO)]
        return remapped

    def _high_contrast(self, palette: np.ndarray) -> np.ndarray:
        hues = np.linspace(0, 255, num=len(palette), endpoint=False)
        remapped = np.zeros_like(palette)
        for index, hue in enumerate(hues):
            remapped[index] = self._hsv_to_rgb(float(hue), 220, 230)
        return remapped

    def _hsv_to_rgb(self, h: float, s: float, v: float) -> np.ndarray:
        r, g, b = colorsys.hsv_to_rgb(h / 255.0, s / 255.0, v / 255.0)
        return np.array([int(r * 255), int(g * 255), int(b * 255)], dtype=np.uint8)
