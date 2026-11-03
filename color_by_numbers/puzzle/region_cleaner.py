import cv2
import numpy as np
from scipy.ndimage import distance_transform_edt


class RegionCleaner:
    def merge_small_regions(
        self,
        label_map: np.ndarray,
        region_color_id: dict[int, int],
        min_area: int,
        max_regions: int | None = None,
    ) -> tuple[np.ndarray, dict[int, int]]:
        labels = label_map.copy()
        colors = dict(region_color_id)
        labels, colors = self._keep_regions(
            labels,
            colors,
            self._large_region_ids(colors, np.bincount(labels.ravel()), min_area),
        )
        if max_regions is not None and len(colors) > max_regions:
            areas = np.bincount(labels.ravel())
            ranked = sorted(
                colors,
                key=lambda region_id: int(areas[region_id]) if region_id < len(areas) else 0,
                reverse=True,
            )
            labels, colors = self._keep_regions(labels, colors, ranked[:max_regions])
        return self._reindex(labels, colors)

    def _keep_regions(
        self,
        labels: np.ndarray,
        colors: dict[int, int],
        keep_ids: list[int],
    ) -> tuple[np.ndarray, dict[int, int]]:
        if not keep_ids:
            return labels, colors
        keep_ids = [region_id for region_id in keep_ids if region_id in colors]
        known = np.isin(labels, keep_ids)
        if not known.any():
            return labels, colors
        if known.all():
            return labels, {region_id: colors[region_id] for region_id in keep_ids}
        preferred = self._same_color_targets(labels, colors, keep_ids)
        _distances, indices = distance_transform_edt(~known, return_distances=True, return_indices=True)
        filled = labels.copy()
        unknown = ~known
        nearest = labels[indices[0][unknown], indices[1][unknown]]
        ys, xs = np.nonzero(unknown)
        for y, x, fallback in zip(ys.tolist(), xs.tolist(), nearest.tolist(), strict=False):
            region_id = int(labels[y, x])
            filled[y, x] = preferred.get(region_id, int(fallback))
        kept = {region_id: colors[region_id] for region_id in keep_ids}
        return filled, kept

    def _same_color_targets(
        self,
        labels: np.ndarray,
        colors: dict[int, int],
        keep_ids: list[int],
    ) -> dict[int, int]:
        keep_set = set(keep_ids)
        targets: dict[int, int] = {}
        kernel = np.ones((3, 3), dtype=np.uint8)
        for region_id, color_id in colors.items():
            if region_id in keep_set:
                continue
            mask = (labels == region_id).astype(np.uint8)
            if not mask.any():
                continue
            dilated = cv2.dilate(mask, kernel).astype(bool)
            border = dilated & ~mask.astype(bool)
            neighbors = labels[border]
            neighbors = neighbors[(neighbors != region_id) & (neighbors != 0)]
            same = [int(n) for n in neighbors if int(n) in keep_set and colors.get(int(n)) == color_id]
            if same:
                values, counts = np.unique(same, return_counts=True)
                targets[region_id] = int(values[int(np.argmax(counts))])
        return targets

    def _large_region_ids(
        self,
        region_color_id: dict[int, int],
        areas: np.ndarray,
        min_area: int,
    ) -> list[int]:
        keep = [
            region_id
            for region_id in region_color_id
            if region_id < len(areas) and int(areas[region_id]) >= min_area
        ]
        if keep:
            return keep
        best = max(
            region_color_id,
            key=lambda region_id: int(areas[region_id]) if region_id < len(areas) else 0,
        )
        return [best]

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
