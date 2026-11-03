from dataclasses import dataclass


@dataclass(frozen=True)
class PaperSize:
    name: str
    width_px: int
    height_px: int


class PrintPageLayout:
    """Page geometry at 150 DPI for common paper sizes."""

    A4 = PaperSize('A4', width_px=1240, height_px=1754)
    LETTER = PaperSize('Letter', width_px=1275, height_px=1650)

    def __init__(self, paper: PaperSize = A4, bleed_px: int = 12, safe_px: int = 36) -> None:
        self.paper = paper
        self.bleed_px = bleed_px
        self.safe_px = safe_px

    @property
    def content_box(self) -> tuple[int, int, int, int]:
        left = self.bleed_px + self.safe_px
        top = self.bleed_px + self.safe_px
        right = self.paper.width_px - left
        bottom = self.paper.height_px - top
        return left, top, right, bottom

    def fit_size(self, width: int, height: int) -> tuple[int, int]:
        left, top, right, bottom = self.content_box
        box_w = max(1, right - left)
        box_h = max(1, bottom - top)
        scale = min(box_w / float(width), box_h / float(height))
        return max(1, int(round(width * scale))), max(1, int(round(height * scale)))
