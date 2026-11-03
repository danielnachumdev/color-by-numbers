from dataclasses import dataclass, field

import numpy as np


@dataclass
class Puzzle:
    label_map: np.ndarray
    region_color_id: dict[int, int]
    palette: np.ndarray
    outlines: np.ndarray
    number_anchors: dict[int, tuple[int, int]]
    preview: np.ndarray
    boundary_paths: list[np.ndarray] = field(default_factory=list)
    filled_regions: set[int] = field(default_factory=set)

    def region_at(self, x: int, y: int) -> int | None:
        height, width = self.label_map.shape
        if x < 0 or y < 0 or x >= width or y >= height:
            return None
        region_id = int(self.label_map[y, x])
        if region_id == 0:
            return None
        return region_id

    def try_fill(self, x: int, y: int, palette_index: int) -> bool:
        region_id = self.region_at(x, y)
        if region_id is None:
            return False
        if self.region_color_id[region_id] != palette_index:
            return False
        if region_id in self.filled_regions:
            return False
        self.filled_regions.add(region_id)
        return True

    def progress(self) -> tuple[int, int]:
        total = len(self.region_color_id)
        return len(self.filled_regions), total

    def is_complete(self) -> bool:
        filled, total = self.progress()
        return total > 0 and filled == total

    def player_number(self, region_id: int) -> int:
        return self.region_color_id[region_id] + 1
