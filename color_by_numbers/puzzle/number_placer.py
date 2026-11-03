import numpy as np


class NumberPlacer:
    def place(self, label_map: np.ndarray, region_color_id: dict[int, int]) -> dict[int, tuple[int, int]]:
        anchors: dict[int, tuple[int, int]] = {}
        for region_id in region_color_id:
            ys, xs = np.where(label_map == region_id)
            if len(xs) == 0:
                continue
            x = int(np.round(xs.mean()))
            y = int(np.round(ys.mean()))
            anchors[region_id] = (x, y)
        return anchors
