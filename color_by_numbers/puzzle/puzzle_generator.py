from collections.abc import Callable
from threading import Event, Thread

import cv2
import numpy as np

from .generation_progress import GenerationProgress
from .number_placer import NumberPlacer
from .outline_builder import OutlineBuilder
from .palette_quantizer import PaletteQuantizer
from .puzzle import Puzzle
from .region_cleaner import RegionCleaner
from .region_labeler import RegionLabeler
from .shared_boundary_tracer import SharedBoundaryTracer

ProgressCallback = Callable[[float, str, float | None, float], None]


class PuzzleGenerator:
    _MIN_AREA_FRACTION = 0.0025
    _MIN_AREA_FLOOR = 120

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
        min_region_area: int | None = None,
        max_side: int = 256,
        progress: ProgressCallback | None = None,
        cancel_event: Event | None = None,
        tracker: GenerationProgress | None = None,
    ) -> Puzzle:
        progress_tracker = tracker or GenerationProgress(include_download=False)
        report = progress or (lambda _f, _m, _e, _elapsed: None)
        stop_pulse = Event()

        def stage(message: str) -> None:
            self._raise_if_cancelled(cancel_event)
            report(*progress_tracker.begin_stage(message))

        def pulse_loop() -> None:
            while not stop_pulse.wait(0.15):
                report(*progress_tracker.pulse())

        pulser = Thread(target=pulse_loop, daemon=True)
        pulser.start()
        try:
            stage('Resizing…')
            rgb = self._resize_to_max_side(rgb, max_side)
            stage('Quantizing colors…')
            index_map, palette = self._quantizer.quantize(rgb, n_colors)
            stage('Finding regions…')
            label_map, region_color_id = self._labeler.label(index_map, n_colors)
            stage('Merging tiny regions…')
            cutoff = self._area_cutoff(rgb.shape, min_region_area)
            label_map, region_color_id = self._cleaner.merge_small_regions(
                label_map, region_color_id, cutoff
            )
            stage('Building outlines…')
            outlines = self._outline_builder.build(label_map)
            anchors = self._number_placer.place(label_map, region_color_id)
            stage('Smoothing borders…')
            boundary_paths = self._boundary_tracer.trace(label_map)
            preview = self._build_preview(label_map, region_color_id, palette, rgb.shape)
            self._raise_if_cancelled(cancel_event)
            report(*progress_tracker.finish_generate())
            return Puzzle(
                label_map=label_map,
                region_color_id=region_color_id,
                palette=palette,
                outlines=outlines,
                number_anchors=anchors,
                preview=preview,
                boundary_paths=boundary_paths,
            )
        finally:
            stop_pulse.set()

    def _raise_if_cancelled(self, cancel_event: Event | None) -> None:
        if cancel_event is not None and cancel_event.is_set():
            raise InterruptedError('Puzzle generation cancelled')

    def _area_cutoff(self, shape: tuple[int, ...], min_region_area: int | None) -> int:
        height, width = shape[:2]
        relative = int(self._MIN_AREA_FRACTION * height * width)
        floor = max(self._MIN_AREA_FLOOR, relative)
        if min_region_area is None:
            return floor
        return max(min_region_area, floor)

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
        if not region_color_id:
            return np.full(shape, 255, dtype=np.uint8)
        color_lookup = np.zeros((max(region_color_id) + 1, 3), dtype=np.uint8)
        for region_id, color_id in region_color_id.items():
            color_lookup[region_id] = palette[color_id]
        return color_lookup[label_map]
