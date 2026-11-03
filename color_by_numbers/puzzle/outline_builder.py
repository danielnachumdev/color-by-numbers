import numpy as np


class OutlineBuilder:
    def build(self, label_map: np.ndarray) -> np.ndarray:
        outlines = np.zeros(label_map.shape, dtype=np.uint8)
        outlines[:, :-1] |= (label_map[:, :-1] != label_map[:, 1:]).astype(np.uint8)
        outlines[:-1, :] |= (label_map[:-1, :] != label_map[1:, :]).astype(np.uint8)
        return outlines
