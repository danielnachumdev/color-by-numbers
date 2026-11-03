import numpy as np


class RegionCleaner:
    def merge_small_regions(
        self,
        label_map: np.ndarray,
        region_color_id: dict[int, int],
        min_area: int,
    ) -> tuple[np.ndarray, dict[int, int]]:
        cleaned = label_map.copy()
        colors = dict(region_color_id)
        while True:
            small_id = self._smallest_below_min(cleaned, colors, min_area)
            if small_id is None:
                break
            neighbor_id = self._dominant_neighbor(cleaned, small_id)
            if neighbor_id is None:
                break
            cleaned[cleaned == small_id] = neighbor_id
            del colors[small_id]
        return self._reindex(cleaned, colors)

    def _smallest_below_min(
        self,
        label_map: np.ndarray,
        region_color_id: dict[int, int],
        min_area: int,
    ) -> int | None:
        areas = {
            region_id: int(np.count_nonzero(label_map == region_id))
            for region_id in region_color_id
        }
        candidates = [region_id for region_id, area in areas.items() if area < min_area]
        if not candidates:
            return None
        return min(candidates, key=lambda region_id: areas[region_id])

    def _dominant_neighbor(self, label_map: np.ndarray, region_id: int) -> int | None:
        height, width = label_map.shape
        ys, xs = np.where(label_map == region_id)
        neighbor_counts: dict[int, int] = {}
        for y, x in zip(ys, xs):
            for dy, dx in ((0, 1), (1, 0), (0, -1), (-1, 0)):
                ny, nx = y + dy, x + dx
                if ny < 0 or nx < 0 or ny >= height or nx >= width:
                    continue
                neighbor_id = int(label_map[ny, nx])
                if neighbor_id == 0 or neighbor_id == region_id:
                    continue
                neighbor_counts[neighbor_id] = neighbor_counts.get(neighbor_id, 0) + 1
        if not neighbor_counts:
            return None
        return max(neighbor_counts, key=neighbor_counts.get)

    def _reindex(
        self,
        label_map: np.ndarray,
        region_color_id: dict[int, int],
    ) -> tuple[np.ndarray, dict[int, int]]:
        remapped = np.zeros_like(label_map)
        new_colors: dict[int, int] = {}
        next_id = 1
        for old_id in sorted(region_color_id):
            remapped[label_map == old_id] = next_id
            new_colors[next_id] = region_color_id[old_id]
            next_id += 1
        return remapped, new_colors
