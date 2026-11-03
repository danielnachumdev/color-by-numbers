import numpy as np
from scipy.ndimage import distance_transform_edt


class RegionCleaner:
    def merge_small_regions(
        self,
        label_map: np.ndarray,
        region_color_id: dict[int, int],
        min_area: int,
    ) -> tuple[np.ndarray, dict[int, int]]:
        labels = label_map.copy()
        areas = np.bincount(labels.ravel())
        keep_ids = self._large_region_ids(region_color_id, areas, min_area)
        if not keep_ids:
            return self._reindex(labels, region_color_id)

        known = np.isin(labels, keep_ids)
        if not known.any():
            return self._reindex(labels, region_color_id)
        if known.all():
            kept_colors = {region_id: region_color_id[region_id] for region_id in keep_ids}
            return self._reindex(labels, kept_colors)

        _distances, indices = distance_transform_edt(~known, return_distances=True, return_indices=True)
        filled = labels.copy()
        unknown = ~known
        filled[unknown] = labels[indices[0][unknown], indices[1][unknown]]
        kept_colors = {region_id: region_color_id[region_id] for region_id in keep_ids}
        return self._reindex(filled, kept_colors)

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
        # Nothing met the cutoff — keep the single largest region as a seed.
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
