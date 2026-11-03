class CanvasViewTransform:
    """Maps puzzle pixels ↔ canvas coords with fit-to-viewport zoom and pan."""

    _MIN_ZOOM = 0.25
    _MAX_ZOOM = 8.0

    def __init__(self) -> None:
        self._content_width = 0
        self._content_height = 0
        self._viewport_width = 0
        self._viewport_height = 0
        self._zoom = 1.0
        self._offset_x = 0.0
        self._offset_y = 0.0

    def set_content_size(self, width: int, height: int) -> None:
        self._content_width = max(0, width)
        self._content_height = max(0, height)

    def set_viewport_size(self, width: int, height: int) -> None:
        self._viewport_width = max(0, width)
        self._viewport_height = max(0, height)

    def reset(self) -> None:
        self._zoom = 1.0
        self._offset_x = 0.0
        self._offset_y = 0.0

    def fit_scale(self) -> float:
        if self._content_width <= 0 or self._content_height <= 0:
            return 1.0
        if self._viewport_width <= 0 or self._viewport_height <= 0:
            return 1.0
        return min(
            self._viewport_width / self._content_width,
            self._viewport_height / self._content_height,
        )

    def display_scale(self) -> float:
        return self.fit_scale() * self._zoom

    def zoom(self) -> float:
        return self._zoom

    def displayed_size(self) -> tuple[int, int]:
        scale = self.display_scale()
        return (
            max(1, int(self._content_width * scale)),
            max(1, int(self._content_height * scale)),
        )

    def image_origin(self) -> tuple[float, float]:
        displayed_width, displayed_height = self.displayed_size()
        origin_x = (self._viewport_width - displayed_width) / 2 + self._offset_x
        origin_y = (self._viewport_height - displayed_height) / 2 + self._offset_y
        return origin_x, origin_y

    def canvas_to_content(self, canvas_x: float, canvas_y: float) -> tuple[int, int] | None:
        scale = self.display_scale()
        if scale <= 0 or self._content_width <= 0 or self._content_height <= 0:
            return None
        origin_x, origin_y = self.image_origin()
        content_x = int((canvas_x - origin_x) / scale)
        content_y = int((canvas_y - origin_y) / scale)
        if not self._in_content_bounds(content_x, content_y):
            return None
        return content_x, content_y

    def zoom_by(self, factor: float, pivot_x: float, pivot_y: float) -> None:
        scale_before = self.display_scale()
        if scale_before <= 0:
            return
        origin_x, origin_y = self.image_origin()
        content_x = (pivot_x - origin_x) / scale_before
        content_y = (pivot_y - origin_y) / scale_before
        self._zoom = self._clamped_zoom(self._zoom * factor)
        self._anchor_content_at_pivot(content_x, content_y, pivot_x, pivot_y)

    def zoom_toward_center(self, factor: float) -> None:
        self.zoom_by(factor, self._viewport_width / 2, self._viewport_height / 2)

    def pan_by(self, delta_x: float, delta_y: float) -> None:
        self._offset_x += delta_x
        self._offset_y += delta_y

    def _anchor_content_at_pivot(
        self,
        content_x: float,
        content_y: float,
        pivot_x: float,
        pivot_y: float,
    ) -> None:
        scale = self.display_scale()
        displayed_width, displayed_height = self.displayed_size()
        desired_origin_x = pivot_x - content_x * scale
        desired_origin_y = pivot_y - content_y * scale
        self._offset_x = desired_origin_x - (self._viewport_width - displayed_width) / 2
        self._offset_y = desired_origin_y - (self._viewport_height - displayed_height) / 2

    def _clamped_zoom(self, zoom: float) -> float:
        return min(self._MAX_ZOOM, max(self._MIN_ZOOM, zoom))

    def _in_content_bounds(self, content_x: int, content_y: int) -> bool:
        return 0 <= content_x < self._content_width and 0 <= content_y < self._content_height
