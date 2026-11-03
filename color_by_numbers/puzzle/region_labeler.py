import cv2
import numpy as np


class RegionLabeler:
    def label(self, index_map: np.ndarray, n_colors: int) -> tuple[np.ndarray, dict[int, int]]:
        label_map = np.zeros(index_map.shape, dtype=np.int32)
        region_color_id: dict[int, int] = {}
        next_region_id = 1
        for color_id in range(n_colors):
            mask = (index_map == color_id).astype(np.uint8)
            component_count, components = cv2.connectedComponents(mask, connectivity=8)
            for component_id in range(1, component_count):
                pixels = components == component_id
                label_map[pixels] = next_region_id
                region_color_id[next_region_id] = color_id
                next_region_id += 1
        return label_map, region_color_id
