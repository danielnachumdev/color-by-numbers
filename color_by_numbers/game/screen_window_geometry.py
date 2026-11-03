class ScreenWindowGeometry:
    """Initial tk window size/placement from the primary screen."""

    def __init__(self, width_fraction: float = 0.9, height_fraction: float = 0.9) -> None:
        self._width_fraction = width_fraction
        self._height_fraction = height_fraction

    def geometry_string(self, screen_width: int, screen_height: int) -> str:
        width = max(640, int(screen_width * self._width_fraction))
        height = max(480, int(screen_height * self._height_fraction))
        width = min(width, screen_width)
        height = min(height, screen_height)
        x = max(0, (screen_width - width) // 2)
        y = max(0, (screen_height - height) // 2)
        return f'{width}x{height}+{x}+{y}'
