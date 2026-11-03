import numpy as np


class ContourSmoother:
    def smooth(self, points: np.ndarray, iterations: int = 5) -> np.ndarray:
        pts = points.reshape(-1, 2).astype(np.float64)
        if len(pts) < 4:
            return pts
        for _ in range(iterations):
            pts = self._chaikin_closed(pts)
        return pts

    def _chaikin_closed(self, points: np.ndarray) -> np.ndarray:
        count = len(points)
        refined = np.empty((count * 2, 2), dtype=np.float64)
        for index in range(count):
            current = points[index]
            nxt = points[(index + 1) % count]
            refined[index * 2] = 0.75 * current + 0.25 * nxt
            refined[index * 2 + 1] = 0.25 * current + 0.75 * nxt
        return refined
