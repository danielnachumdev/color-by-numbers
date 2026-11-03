import tempfile
import unittest
from pathlib import Path

import numpy as np

from color_by_numbers.game.print_page_layout import PrintPageLayout
from color_by_numbers.game.print_sheet_composer import PrintSheetComposer
from color_by_numbers.game.sheet_exporter import SheetExporter
from color_by_numbers.i18n import UiStrings
from color_by_numbers.persistence.app_settings import AppSettings
from color_by_numbers.puzzle.puzzle import Puzzle
from color_by_numbers.puzzle.puzzle_generator import PuzzleGenerator
from color_by_numbers.puzzle.region_cleaner import RegionCleaner


class TestMultiPagePrintAndSettings(unittest.TestCase):
    def _puzzle(self):
        image = np.zeros((48, 64, 3), dtype=np.uint8)
        image[:, :32] = (200, 40, 40)
        image[:, 32:] = (40, 40, 200)
        return PuzzleGenerator().generate(image, n_colors=2, min_region_area=10, max_side=64)

    def test_compose_pages_a4_two_pages(self):
        puzzle = self._puzzle()
        pages = PrintSheetComposer(layout=PrintPageLayout(PrintPageLayout.A4)).compose_pages(
            puzzle,
            palette_on_second_page=True,
        )
        self.assertEqual(len(pages), 2)
        self.assertEqual(pages[0].shape[1], PrintPageLayout.A4.width_px)
        self.assertEqual(pages[0].shape[0], PrintPageLayout.A4.height_px)

    def test_export_pdf_multipage(self):
        puzzle = self._puzzle()
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / 'pages.pdf'
            SheetExporter().export_pdf(path, puzzle, paper='Letter', palette_on_second_page=True)
            self.assertTrue(path.exists())
            self.assertGreater(path.stat().st_size, 0)

    def test_app_settings_round_trip(self):
        with tempfile.TemporaryDirectory() as tmp:
            settings = AppSettings(path=Path(tmp) / 'settings.json')
            settings.update({'paint_mode': True, 'language': 'he'})
            loaded = AppSettings(path=Path(tmp) / 'settings.json')
            self.assertTrue(loaded.get('paint_mode'))
            self.assertEqual(loaded.get('language'), 'he')

    def test_ui_strings_hebrew_rtl(self):
        strings = UiStrings('he')
        self.assertTrue(strings.rtl)
        self.assertIn('חידה', strings.t('new_puzzle'))


class TestRegionQualityAndReplay(unittest.TestCase):
    def test_max_regions_cap(self):
        label_map = np.arange(1, 17, dtype=np.int32).reshape(4, 4)
        colors = {int(v): int(v) % 3 for v in label_map.ravel()}
        cleaned, kept = RegionCleaner().merge_small_regions(label_map, colors, min_area=1, max_regions=4)
        self.assertLessEqual(len(kept), 4)
        self.assertEqual(set(np.unique(cleaned)) - {0}, set(kept))

    def test_fill_history_and_replay_frames(self):
        puzzle = Puzzle(
            label_map=np.array([[1, 2], [3, 3]], dtype=np.int32),
            region_color_id={1: 0, 2: 1, 3: 0},
            palette=np.array([[255, 0, 0], [0, 255, 0]], dtype=np.uint8),
            outlines=np.zeros((2, 2), dtype=np.uint8),
            number_anchors={1: (0, 0), 2: (1, 0), 3: (0, 1)},
            preview=np.zeros((2, 2, 3), dtype=np.uint8),
        )
        self.assertEqual(puzzle.try_fill(0, 0, 0), 1)
        self.assertEqual(puzzle.try_fill(1, 0, 1), 2)
        self.assertEqual(puzzle.fill_history, [1, 2])
        frames = puzzle.replay_frames()
        self.assertEqual(frames[0], set())
        self.assertEqual(frames[-1], {1, 2})
        puzzle.undo()
        self.assertEqual(puzzle.fill_history, [1])

    def test_skin_bias_generate(self):
        image = np.zeros((60, 60, 3), dtype=np.uint8)
        image[:] = (40, 40, 200)
        image[20:40, 20:40] = (200, 160, 140)
        puzzle = PuzzleGenerator().generate(
            image,
            n_colors=3,
            max_side=60,
            skin_bias=True,
            max_regions=20,
        )
        self.assertGreaterEqual(len(puzzle.region_color_id), 1)
        self.assertLessEqual(len(puzzle.region_color_id), 20)


if __name__ == '__main__':
    unittest.main()
