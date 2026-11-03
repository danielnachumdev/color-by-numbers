import cv2
import numpy as np


class PaletteQuantizer:
    _SAMPLE_CAP = 12_000

    def quantize(
        self,
        rgb: np.ndarray,
        n_colors: int,
        random_seed: int = 42,
        *,
        edge_aware: bool = True,
        preserve_detail: bool = False,
        locked_palette: np.ndarray | None = None,
    ) -> tuple[np.ndarray, np.ndarray]:
        if locked_palette is not None and len(locked_palette) > 0:
            return self._quantize_locked(rgb, locked_palette, preserve_detail=preserve_detail)
        lab = cv2.cvtColor(rgb, cv2.COLOR_RGB2Lab)
        pixels = lab.reshape((-1, 3)).astype(np.float32)
        cluster_count = min(n_colors, len(pixels))
        sample = self._sample_pixels(rgb, pixels, random_seed, edge_aware=edge_aware)
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
        index_map = self._despeckle(index_map, preserve_detail=preserve_detail)
        palette = self._palette_from_labels(rgb, index_map.reshape(-1), cluster_count)
        return index_map.astype(np.int32), palette

    def _quantize_locked(
        self,
        rgb: np.ndarray,
        locked_palette: np.ndarray,
        *,
        preserve_detail: bool,
    ) -> tuple[np.ndarray, np.ndarray]:
        palette = locked_palette.astype(np.uint8)
        lab_image = cv2.cvtColor(rgb, cv2.COLOR_RGB2Lab).reshape((-1, 3)).astype(np.float32)
        lab_palette = cv2.cvtColor(palette.reshape(1, -1, 3), cv2.COLOR_RGB2Lab).reshape((-1, 3)).astype(np.float32)
        labels = self._assign_nearest(lab_image, lab_palette)
        index_map = labels.reshape(rgb.shape[:2]).astype(np.uint8)
        index_map = self._despeckle(index_map, preserve_detail=preserve_detail)
        return index_map.astype(np.int32), palette.copy()

    def _sample_pixels(
        self,
        rgb: np.ndarray,
        pixels: np.ndarray,
        random_seed: int,
        *,
        edge_aware: bool,
    ) -> np.ndarray:
        if len(pixels) <= self._SAMPLE_CAP:
            return pixels
        rng = np.random.default_rng(random_seed)
        if not edge_aware:
            choice = rng.choice(len(pixels), size=self._SAMPLE_CAP, replace=False)
            return pixels[choice]
        gray = cv2.cvtColor(rgb, cv2.COLOR_RGB2GRAY)
        edges = cv2.Canny(gray, 80, 160).reshape(-1).astype(np.float64)
        weights = edges + 1.0
        weights /= weights.sum()
        choice = rng.choice(len(pixels), size=self._SAMPLE_CAP, replace=False, p=weights)
        return pixels[choice]

    def _despeckle(self, index_map: np.ndarray, *, preserve_detail: bool) -> np.ndarray:
        if preserve_detail:
            return cv2.medianBlur(index_map, 3)
        blurred = cv2.medianBlur(index_map, 5)
        return cv2.medianBlur(blurred, 5)

    def _assign_nearest(self, pixels: np.ndarray, centers: np.ndarray) -> np.ndarray:
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
