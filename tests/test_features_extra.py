import tempfile
import unittest
from pathlib import Path

import numpy as np

from color_by_numbers.game.color_blind_palette import ColorBlindPalette
from color_by_numbers.game.difficulty_preset import DifficultyPresets
from color_by_numbers.game.play_timer import PlayTimer
from color_by_numbers.game.print_sheet_composer import PrintSheetComposer
from color_by_numbers.game.sheet_exporter import SheetExporter
from color_by_numbers.persistence.autosave_store import AutosaveStore
from color_by_numbers.puzzle.palette_quantizer import PaletteQuantizer
from color_by_numbers.puzzle.puzzle_generator import PuzzleGenerator


class TestPrintAndAutosave(unittest.TestCase):
    def _puzzle(self):
        image = np.zeros((48, 64, 3), dtype=np.uint8)
        image[:, :32] = (200, 40, 40)
        image[:, 32:] = (40, 40, 200)
        return PuzzleGenerator().generate(image, n_colors=2, min_region_area=10, max_side=64)

    def test_print_sheet_has_margins(self):
        puzzle = self._puzzle()
        page = PrintSheetComposer(margin=20, cut_mark=8).compose(puzzle)
        self.assertGreater(page.shape[0], puzzle.label_map.shape[0])
        self.assertGreater(page.shape[1], puzzle.label_map.shape[1])

    def test_export_png_print_ready(self):
        puzzle = self._puzzle()
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / 'print.png'
            SheetExporter().export_png(path, puzzle, print_ready=True)
            self.assertTrue(path.exists())
            self.assertGreater(path.stat().st_size, 0)

    def test_autosave_round_trip(self):
        puzzle = self._puzzle()
        region_id = next(iter(puzzle.region_color_id))
        puzzle.try_fill(*puzzle.number_anchors[region_id], puzzle.region_color_id[region_id])
        with tempfile.TemporaryDirectory() as tmp:
            store = AutosaveStore(root=Path(tmp))
            store.save_slot(2, puzzle, n_colors=2, label='demo')
            loaded = store.load_slot(2)
            self.assertIsNotNone(loaded)
            restored, n_colors = loaded
            self.assertEqual(n_colors, 2)
            self.assertEqual(restored.filled_regions, puzzle.filled_regions)
            last = store.load_last()
            self.assertIsNotNone(last)
            self.assertEqual(last[2], 2)


class TestSmarterQuantizeAndPlayHelpers(unittest.TestCase):
    def test_locked_palette_reused(self):
        image = np.zeros((40, 40, 3), dtype=np.uint8)
        image[:20] = (10, 20, 30)
        image[20:] = (200, 210, 220)
        locked = np.array([[10, 20, 30], [200, 210, 220]], dtype=np.uint8)
        _index_map, palette = PaletteQuantizer().quantize(image, 2, locked_palette=locked)
        self.assertTrue(np.array_equal(palette, locked))

    def test_edge_aware_generate(self):
        image = np.zeros((60, 60, 3), dtype=np.uint8)
        image[:30] = (220, 30, 30)
        image[30:] = (30, 30, 220)
        puzzle = PuzzleGenerator().generate(
            image,
            n_colors=2,
            max_side=60,
            edge_aware=True,
            preserve_detail=True,
        )
        self.assertGreaterEqual(len(puzzle.region_color_id), 1)

    def test_color_blind_remap_keeps_length(self):
        palette = np.array([[10, 20, 30], [200, 100, 50], [0, 255, 0]], dtype=np.uint8)
        remapped = ColorBlindPalette().remap(palette, 'Deuteranopia')
        self.assertEqual(remapped.shape, palette.shape)

    def test_play_timer_score(self):
        timer = PlayTimer()
        timer.record_fill()
        timer.record_fill()
        self.assertGreater(timer.score(10), 0)
        self.assertIn('Time', timer.summary(10))

    def test_kids_preset_exists(self):
        names = {preset.name for preset in DifficultyPresets.all()}
        self.assertIn('Kids', names)


class TestEntrypointSmoke(unittest.TestCase):
    def test_package_exports_and_main(self):
        import color_by_numbers
        from color_by_numbers.__main__ import main

        self.assertTrue(hasattr(color_by_numbers, 'PuzzleGenerator'))
        self.assertTrue(callable(main))


if __name__ == '__main__':
    unittest.main()
