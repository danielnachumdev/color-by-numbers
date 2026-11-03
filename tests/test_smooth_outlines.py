import unittest

import numpy as np

from color_by_numbers.game.sheet_renderer import SheetRenderer
from color_by_numbers.puzzle.contour_smoother import ContourSmoother
from color_by_numbers.puzzle.puzzle import Puzzle
from color_by_numbers.puzzle.region_contour_extractor import RegionContourExtractor


class TestContourSmoother(unittest.TestCase):
    def test_chaikin_increases_point_count(self):
        square = np.array([[0, 0], [10, 0], [10, 10], [0, 10]], dtype=np.float64)
        smoothed = ContourSmoother().smooth(square, iterations=2)
        self.assertGreater(len(smoothed), len(square))


class TestRegionContourExtractor(unittest.TestCase):
    def test_extracts_smoothed_contour_per_region(self):
        label_map = np.zeros((40, 40), dtype=np.int32)
        label_map[5:20, 5:20] = 1
        label_map[5:20, 20:35] = 2
        contours = RegionContourExtractor().extract(label_map, {1: 0, 2: 1})
        self.assertEqual(set(contours), {1, 2})
        self.assertGreaterEqual(len(contours[1]), 4)


class TestSheetRenderer(unittest.TestCase):
    def test_renders_above_min_side_with_smooth_contours(self):
        label_map = np.zeros((50, 80), dtype=np.int32)
        label_map[:, :40] = 1
        label_map[:, 40:] = 2
        extractor = RegionContourExtractor()
        contours = extractor.extract(label_map, {1: 0, 2: 1})
        puzzle = Puzzle(
            label_map=label_map,
            region_color_id={1: 0, 2: 1},
            palette=np.array([[255, 0, 0], [0, 255, 0]], dtype=np.uint8),
            outlines=np.zeros_like(label_map, dtype=np.uint8),
            number_anchors={1: (20, 25), 2: (60, 25)},
            preview=np.zeros((50, 80, 3), dtype=np.uint8),
            contours=contours,
        )
        renderer = SheetRenderer(base_scale=2, min_side=400)
        sheet = renderer.render(puzzle)
        self.assertGreaterEqual(max(sheet.shape[0], sheet.shape[1]), 400)
        self.assertEqual(renderer.content_scale, 5)
        self.assertTrue((sheet == 0).any())


if __name__ == '__main__':
    unittest.main()
