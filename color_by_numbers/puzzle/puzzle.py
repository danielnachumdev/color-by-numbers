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
    _undo_stack: list[int] = field(default_factory=list, repr=False)
    _redo_stack: list[int] = field(default_factory=list, repr=False)

    def region_at(self, x: int, y: int) -> int | None:
        height, width = self.label_map.shape
        if x < 0 or y < 0 or x >= width or y >= height:
            return None
        region_id = int(self.label_map[y, x])
        if region_id == 0:
            return None
        return region_id

    def try_fill(self, x: int, y: int, palette_index: int) -> int | None:
        region_id = self.region_at(x, y)
        if region_id is None:
            return None
        if self.region_color_id[region_id] != palette_index:
            return None
        if region_id in self.filled_regions:
            return None
        self.filled_regions.add(region_id)
        self._undo_stack.append(region_id)
        self._redo_stack.clear()
        return region_id

    def undo(self) -> int | None:
        if not self._undo_stack:
            return None
        region_id = self._undo_stack.pop()
        self.filled_regions.discard(region_id)
        self._redo_stack.append(region_id)
        return region_id

    def redo(self) -> int | None:
        if not self._redo_stack:
            return None
        region_id = self._redo_stack.pop()
        self.filled_regions.add(region_id)
        self._undo_stack.append(region_id)
        return region_id

    def progress(self) -> tuple[int, int]:
        total = len(self.region_color_id)
        return len(self.filled_regions), total

    def progress_percent(self) -> float:
        filled, total = self.progress()
        if total == 0:
            return 0.0
        return 100.0 * filled / total

    def remaining_for_color(self, palette_index: int) -> int:
        return len(self.unfilled_regions_for_color(palette_index))

    def unfilled_regions_for_color(self, palette_index: int) -> list[int]:
        return [
            region_id
            for region_id, color_id in self.region_color_id.items()
            if color_id == palette_index and region_id not in self.filled_regions
        ]

    def color_is_complete(self, palette_index: int) -> bool:
        return self.remaining_for_color(palette_index) == 0

    def next_incomplete_color(self, after_index: int) -> int | None:
        color_count = len(self.palette)
        for offset in range(1, color_count + 1):
            candidate = (after_index + offset) % color_count
            if not self.color_is_complete(candidate):
                return candidate
        return None

    def is_complete(self) -> bool:
        filled, total = self.progress()
        return total > 0 and filled == total

    def player_number(self, region_id: int) -> int:
        return self.region_color_id[region_id] + 1

    def status_summary(self, selected_color: int) -> str:
        filled, total = self.progress()
        remaining = self.remaining_for_color(selected_color)
        return (
            f'Color {selected_color + 1}: {remaining} left — '
            f'{filled}/{total} ({self.progress_percent():.0f}%)'
        )
