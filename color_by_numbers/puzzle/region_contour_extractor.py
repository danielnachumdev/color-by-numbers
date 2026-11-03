import cv2
import numpy as np

from .contour_smoother import ContourSmoother


class RegionContourExtractor:
    def __init__(
        self,
        smoother: ContourSmoother | None = None,
        simplify_epsilon: float = 1.25,
        smooth_iterations: int = 5,
    ) -> None:
        self._smoother = smoother or ContourSmoother()
        self._simplify_epsilon = simplify_epsilon
        self._smooth_iterations = smooth_iterations

    def extract(
        self,
        label_map: np.ndarray,
        region_color_id: dict[int, int],
    ) -> dict[int, np.ndarray]:
        contours: dict[int, np.ndarray] = {}
        for region_id in region_color_id:
            mask = (label_map == region_id).astype(np.uint8) * 255
            found, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)
            if not found:
                continue
            largest = max(found, key=cv2.contourArea)
            simplified = cv2.approxPolyDP(largest, self._simplify_epsilon, closed=True)
            contours[region_id] = self._smoother.smooth(
                simplified,
                iterations=self._smooth_iterations,
            )
        return contours
