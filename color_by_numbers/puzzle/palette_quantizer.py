import cv2
import numpy as np


class PaletteQuantizer:
    _SAMPLE_CAP = 12_000

    def quantize(self, rgb: np.ndarray, n_colors: int, random_seed: int = 42) -> tuple[np.ndarray, np.ndarray]:
        lab = cv2.cvtColor(rgb, cv2.COLOR_RGB2Lab)
        pixels = lab.reshape((-1, 3)).astype(np.float32)
        cluster_count = min(n_colors, len(pixels))
        sample = self._sample_pixels(pixels, random_seed)
        cv2.setRNGSeed(random_seed)
        criteria = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 15, 1.0)
        _compactness, _sample_labels, centers = cv2.kmeans(
            sample,
            cluster_count,
            None,
            criteria,
            2,
            cv2.KMEANS_PP_CENTERS,
        )
        labels = self._assign_nearest(pixels, centers.astype(np.float32))
        index_map = labels.reshape(rgb.shape[:2]).astype(np.uint8)
        index_map = cv2.medianBlur(index_map, 5)
        index_map = cv2.medianBlur(index_map, 5)
        palette = self._palette_from_labels(rgb, index_map.reshape(-1), cluster_count)
        return index_map.astype(np.int32), palette

    def _sample_pixels(self, pixels: np.ndarray, random_seed: int) -> np.ndarray:
        if len(pixels) <= self._SAMPLE_CAP:
            return pixels
        rng = np.random.default_rng(random_seed)
        choice = rng.choice(len(pixels), size=self._SAMPLE_CAP, replace=False)
        return pixels[choice]

    def _assign_nearest(self, pixels: np.ndarray, centers: np.ndarray) -> np.ndarray:
        # Chunk to keep peak memory modest on large images.
        labels = np.empty(len(pixels), dtype=np.int32)
        chunk = 50_000
        for start in range(0, len(pixels), chunk):
            end = min(start + chunk, len(pixels))
            diff = pixels[start:end, None, :] - centers[None, :, :]
            dist = np.einsum('ijk,ijk->ij', diff, diff)
            labels[start:end] = np.argmin(dist, axis=1)
        return labels

    def _palette_from_labels(self, rgb: np.ndarray, labels: np.ndarray, n_colors: int) -> np.ndarray:
        flat = rgb.reshape((-1, 3))
        palette = np.zeros((n_colors, 3), dtype=np.uint8)
        for color_id in range(n_colors):
            members = flat[labels == color_id]
            if len(members) == 0:
                continue
            palette[color_id] = np.round(members.mean(axis=0)).astype(np.uint8)
        return palette
