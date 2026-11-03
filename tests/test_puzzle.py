import unittest

import numpy as np

from color_by_numbers.puzzle.outline_builder import OutlineBuilder
from color_by_numbers.puzzle.puzzle import Puzzle
from color_by_numbers.puzzle.puzzle_generator import PuzzleGenerator
from color_by_numbers.puzzle.region_cleaner import RegionCleaner
from color_by_numbers.puzzle.region_labeler import RegionLabeler


class TestPuzzleFill(unittest.TestCase):
    def setUp(self) -> None:
        label_map = np.array([
            [1, 1, 2],
            [1, 1, 2],
            [3, 3, 3],
        ], dtype=np.int32)
        self.puzzle = Puzzle(
            label_map=label_map,
            region_color_id={1: 0, 2: 1, 3: 0},
            palette=np.array([[255, 0, 0], [0, 255, 0]], dtype=np.uint8),
            outlines=np.zeros_like(label_map, dtype=np.uint8),
            number_anchors={1: (0, 0), 2: (2, 0), 3: (1, 2)},
            preview=np.zeros((3, 3, 3), dtype=np.uint8),
        )

    def test_try_fill_accepts_matching_color(self):
        self.assertTrue(self.puzzle.try_fill(0, 0, 0))
        self.assertIn(1, self.puzzle.filled_regions)

    def test_try_fill_rejects_wrong_color(self):
        self.assertFalse(self.puzzle.try_fill(0, 0, 1))
        self.assertEqual(self.puzzle.filled_regions, set())

    def test_try_fill_rejects_repeat(self):
        self.assertTrue(self.puzzle.try_fill(0, 0, 0))
        self.assertFalse(self.puzzle.try_fill(1, 1, 0))

    def test_progress_and_complete(self):
        self.puzzle.try_fill(0, 0, 0)
        self.puzzle.try_fill(2, 0, 1)
        self.assertEqual(self.puzzle.progress(), (2, 3))
        self.assertFalse(self.puzzle.is_complete())
        self.puzzle.try_fill(1, 2, 0)
        self.assertTrue(self.puzzle.is_complete())

    def test_region_at_out_of_bounds(self):
        self.assertIsNone(self.puzzle.region_at(-1, 0))
        self.assertIsNone(self.puzzle.region_at(9, 9))


class TestRegionCleaner(unittest.TestCase):
    def test_merge_reduces_small_regions(self):
        label_map = np.array([
            [1, 1, 1, 2],
            [1, 1, 1, 2],
            [1, 1, 1, 3],
            [1, 1, 1, 3],
        ], dtype=np.int32)
        region_color_id = {1: 0, 2: 1, 3: 1}
        cleaned, colors = RegionCleaner().merge_small_regions(label_map, region_color_id, min_area=5)
        self.assertLess(len(colors), len(region_color_id))
        self.assertEqual(set(np.unique(cleaned)) - {0}, set(colors))


class TestOutlineBuilder(unittest.TestCase):
    def test_outlines_mark_boundaries(self):
        label_map = np.array([
            [1, 1, 2],
            [1, 1, 2],
        ], dtype=np.int32)
        outlines = OutlineBuilder().build(label_map)
        self.assertTrue(outlines.any())
        self.assertTrue(outlines[0, 1] == 1 or outlines[0, 2] == 1)


class TestPuzzleGenerator(unittest.TestCase):
    def _block_image(self) -> np.ndarray:
        image = np.zeros((40, 60, 3), dtype=np.uint8)
        image[:, :20] = (220, 40, 40)
        image[:, 20:40] = (40, 180, 40)
        image[:, 40:] = (40, 40, 220)
        return image

    def test_generate_palette_and_mappings(self):
        puzzle = PuzzleGenerator().generate(self._block_image(), n_colors=3, min_region_area=10, max_side=60)
        self.assertEqual(len(puzzle.palette), 3)
        self.assertTrue(puzzle.outlines.any())
        self.assertGreater(len(puzzle.region_color_id), 0)
        for region_id, color_id in puzzle.region_color_id.items():
            self.assertIn(color_id, range(len(puzzle.palette)))
            x, y = puzzle.number_anchors[region_id]
            self.assertEqual(int(puzzle.label_map[y, x]), region_id)

    def test_area_cutoff_merges_tiny_regions(self):
        image = np.full((80, 80, 3), 200, dtype=np.uint8)
        image[0:2, 0:2] = (10, 10, 10)
        puzzle = PuzzleGenerator().generate(image, n_colors=2, max_side=80)
        areas = [
            int(np.count_nonzero(puzzle.label_map == region_id))
            for region_id in puzzle.region_color_id
        ]
        self.assertTrue(areas)
        self.assertGreaterEqual(min(areas), PuzzleGenerator._MIN_AREA_FLOOR)

    def test_labeler_assigns_color_ids(self):
        index_map = np.array([
            [0, 0, 1],
            [0, 0, 1],
            [2, 2, 2],
        ], dtype=np.int32)
        label_map, region_color_id = RegionLabeler().label(index_map, n_colors=3)
        self.assertEqual(region_color_id[int(label_map[0, 0])], 0)
        self.assertEqual(region_color_id[int(label_map[0, 2])], 1)
        self.assertEqual(region_color_id[int(label_map[2, 0])], 2)


if __name__ == '__main__':
    unittest.main()
