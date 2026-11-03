import cv2
import numpy as np

from .number_placer import NumberPlacer
from .outline_builder import OutlineBuilder
from .palette_quantizer import PaletteQuantizer
from .puzzle import Puzzle
from .region_cleaner import RegionCleaner
from .region_labeler import RegionLabeler
from .shared_boundary_tracer import SharedBoundaryTracer


class PuzzleGenerator:
    def __init__(
        self,
        quantizer: PaletteQuantizer | None = None,
        labeler: RegionLabeler | None = None,
        cleaner: RegionCleaner | None = None,
        outline_builder: OutlineBuilder | None = None,
        number_placer: NumberPlacer | None = None,
        boundary_tracer: SharedBoundaryTracer | None = None,
    ) -> None:
        self._quantizer = quantizer or PaletteQuantizer()
        self._labeler = labeler or RegionLabeler()
        self._cleaner = cleaner or RegionCleaner()
        self._outline_builder = outline_builder or OutlineBuilder()
        self._number_placer = number_placer or NumberPlacer()
        self._boundary_tracer = boundary_tracer or SharedBoundaryTracer()

    def generate(
        self,
        rgb: np.ndarray,
        n_colors: int = 8,
        min_region_area: int = 40,
        max_side: int = 480,
    ) -> Puzzle:
        rgb = self._resize_to_max_side(rgb, max_side)
        index_map, palette = self._quantizer.quantize(rgb, n_colors)
        label_map, region_color_id = self._labeler.label(index_map, n_colors)
        label_map, region_color_id = self._cleaner.merge_small_regions(
            label_map, region_color_id, min_region_area
        )
        outlines = self._outline_builder.build(label_map)
        anchors = self._number_placer.place(label_map, region_color_id)
        boundary_paths = self._boundary_tracer.trace(label_map)
        preview = self._build_preview(label_map, region_color_id, palette, rgb.shape)
        return Puzzle(
            label_map=label_map,
            region_color_id=region_color_id,
            palette=palette,
            outlines=outlines,
            number_anchors=anchors,
            preview=preview,
            boundary_paths=boundary_paths,
        )

    def _resize_to_max_side(self, rgb: np.ndarray, max_side: int) -> np.ndarray:
        height, width = rgb.shape[:2]
        longest = max(height, width)
        if longest <= max_side:
            return rgb
        scale = max_side / float(longest)
        new_size = (int(round(width * scale)), int(round(height * scale)))
        return cv2.resize(rgb, new_size, interpolation=cv2.INTER_AREA)

    def _build_preview(
        self,
        label_map: np.ndarray,
        region_color_id: dict[int, int],
        palette: np.ndarray,
        shape: tuple[int, ...],
    ) -> np.ndarray:
        preview = np.full(shape, 255, dtype=np.uint8)
        for region_id, color_id in region_color_id.items():
            preview[label_map == region_id] = palette[color_id]
        return preview
