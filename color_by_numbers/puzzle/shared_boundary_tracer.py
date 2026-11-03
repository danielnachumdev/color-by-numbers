from collections import defaultdict

import cv2
import numpy as np

from .contour_smoother import ContourSmoother


class SharedBoundaryTracer:
    """Trace each internal shared region border once (no per-region duplicate loops)."""

    def __init__(
        self,
        smoother: ContourSmoother | None = None,
        simplify_epsilon: float = 0.85,
        smooth_iterations: int = 5,
    ) -> None:
        self._smoother = smoother or ContourSmoother()
        self._simplify_epsilon = simplify_epsilon
        self._smooth_iterations = smooth_iterations

    def trace(self, label_map: np.ndarray) -> list[np.ndarray]:
        adjacency = self._build_corner_adjacency(label_map)
        raw_paths = self._chain_paths(adjacency)
        return [self._finalize_path(path) for path in raw_paths if len(path) >= 2]

    def _build_corner_adjacency(self, label_map: np.ndarray) -> dict[tuple[int, int], set[tuple[int, int]]]:
        height, width = label_map.shape
        adjacency: dict[tuple[int, int], set[tuple[int, int]]] = defaultdict(set)
        for y in range(height):
            for x in range(width - 1):
                if label_map[y, x] == label_map[y, x + 1]:
                    continue
                if label_map[y, x] == 0 or label_map[y, x + 1] == 0:
                    continue
                self._add_segment(adjacency, (x + 1, y), (x + 1, y + 1))
        for y in range(height - 1):
            for x in range(width):
                if label_map[y, x] == label_map[y + 1, x]:
                    continue
                if label_map[y, x] == 0 or label_map[y + 1, x] == 0:
                    continue
                self._add_segment(adjacency, (x, y + 1), (x + 1, y + 1))
        return adjacency

    def _add_segment(
        self,
        adjacency: dict[tuple[int, int], set[tuple[int, int]]],
        start: tuple[int, int],
        end: tuple[int, int],
    ) -> None:
        adjacency[start].add(end)
        adjacency[end].add(start)

    def _chain_paths(
        self,
        adjacency: dict[tuple[int, int], set[tuple[int, int]]],
    ) -> list[list[tuple[int, int]]]:
        remaining = {point: set(neighbors) for point, neighbors in adjacency.items()}
        paths: list[list[tuple[int, int]]] = []
        for start in sorted(remaining, key=lambda point: (len(remaining[point]), point)):
            if start not in remaining or len(remaining[start]) != 1:
                continue
            paths.append(self._walk_path(remaining, start))
        while remaining:
            start = next(iter(sorted(remaining)))
            paths.append(self._walk_path(remaining, start))
        return paths

    def _walk_path(
        self,
        remaining: dict[tuple[int, int], set[tuple[int, int]]],
        start: tuple[int, int],
    ) -> list[tuple[int, int]]:
        path = [start]
        current = start
        while current in remaining and remaining[current]:
            nxt = sorted(remaining[current])[0]
            remaining[current].remove(nxt)
            if not remaining[current]:
                del remaining[current]
            if nxt in remaining:
                remaining[nxt].discard(current)
                if not remaining[nxt]:
                    del remaining[nxt]
            path.append(nxt)
            current = nxt
            if current == start and len(path) > 2:
                break
        return path

    def _finalize_path(self, path: list[tuple[int, int]]) -> np.ndarray:
        closed = len(path) > 2 and path[0] == path[-1]
        unique = path[:-1] if closed else path
        points = np.asarray(unique, dtype=np.float32).reshape(-1, 1, 2)
        simplified = cv2.approxPolyDP(points, self._simplify_epsilon, closed=closed)
        return self._smoother.smooth(
            simplified,
            iterations=self._smooth_iterations,
            closed=closed,
        )
