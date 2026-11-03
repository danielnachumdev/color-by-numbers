import cv2
import numpy as np
from sklearn.cluster import KMeans


class PaletteQuantizer:
    def quantize(self, rgb: np.ndarray, n_colors: int, random_seed: int = 42) -> tuple[np.ndarray, np.ndarray]:
        lab = cv2.cvtColor(rgb, cv2.COLOR_RGB2Lab)
        pixels = lab.reshape((-1, 3)).astype(np.float32)
        cluster_count = min(n_colors, len(pixels))
        kmeans = KMeans(n_clusters=cluster_count, random_state=random_seed, n_init=10)
        labels = kmeans.fit_predict(pixels)
        index_map = labels.reshape(rgb.shape[:2]).astype(np.int32)
        palette = self._palette_from_labels(rgb, labels, cluster_count)
        return index_map, palette

    def _palette_from_labels(self, rgb: np.ndarray, labels: np.ndarray, n_colors: int) -> np.ndarray:
        flat = rgb.reshape((-1, 3))
        palette = np.zeros((n_colors, 3), dtype=np.uint8)
        for color_id in range(n_colors):
            members = flat[labels == color_id]
            if len(members) == 0:
                continue
            palette[color_id] = np.round(members.mean(axis=0)).astype(np.uint8)
        return palette
