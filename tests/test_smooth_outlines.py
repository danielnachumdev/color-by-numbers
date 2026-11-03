import unittest

import numpy as np

from color_by_numbers.game.sheet_renderer import SheetRenderer
from color_by_numbers.puzzle.contour_smoother import ContourSmoother
from color_by_numbers.puzzle.puzzle import Puzzle
from color_by_numbers.puzzle.shared_boundary_tracer import SharedBoundaryTracer


class TestContourSmoother(unittest.TestCase):
    def test_chaikin_increases_point_count(self):
        square = np.array([[0, 0], [10, 0], [10, 10], [0, 10]], dtype=np.float64)
        smoothed = ContourSmoother().smooth(square, iterations=5, closed=True)
        self.assertGreater(len(smoothed), len(square) * 8)

    def test_open_chaikin_keeps_endpoints(self):
        line = np.array([[0, 0], [5, 0], [10, 0]], dtype=np.float64)
        smoothed = ContourSmoother().smooth(line, iterations=2, closed=False)
        np.testing.assert_allclose(smoothed[0], line[0])
        np.testing.assert_allclose(smoothed[-1], line[-1])


class TestSharedBoundaryTracer(unittest.TestCase):
    def test_shared_edge_is_traced_once(self):
        label_map = np.zeros((20, 30), dtype=np.int32)
        label_map[:, :15] = 1
        label_map[:, 15:] = 2
        tracer = SharedBoundaryTracer(smooth_iterations=0, simplify_epsilon=0.0)
        adjacency = tracer._build_corner_adjacency(label_map)
        remaining = {point: set(neighbors) for point, neighbors in adjacency.items()}
        raw_paths = tracer._chain_paths(remaining)
        seam_edge_uses = 0
        for path in raw_paths:
            for start, end in zip(path, path[1:]):
                if start[0] == 15 and end[0] == 15:
                    seam_edge_uses += 1
        self.assertEqual(seam_edge_uses, 20)

    def test_two_regions_do_not_emit_two_full_loops(self):
        label_map = np.zeros((40, 40), dtype=np.int32)
        label_map[5:20, 5:20] = 1
        label_map[5:20, 20:35] = 2
        paths = SharedBoundaryTracer().trace(label_map)
        self.assertGreaterEqual(len(paths), 1)
        self.assertLess(len(paths), 8)


class TestSheetRenderer(unittest.TestCase):
    def test_renders_above_min_side_with_shared_boundaries(self):
        label_map = np.zeros((50, 80), dtype=np.int32)
        label_map[:, :40] = 1
        label_map[:, 40:] = 2
        paths = SharedBoundaryTracer().trace(label_map)
        puzzle = Puzzle(
            label_map=label_map,
            region_color_id={1: 0, 2: 1},
            palette=np.array([[255, 0, 0], [0, 255, 0]], dtype=np.uint8),
            outlines=np.zeros_like(label_map, dtype=np.uint8),
            number_anchors={1: (20, 25), 2: (60, 25)},
            preview=np.zeros((50, 80, 3), dtype=np.uint8),
            boundary_paths=paths,
        )
        renderer = SheetRenderer(base_scale=2, min_side=400)
        sheet = renderer.render(puzzle)
        self.assertGreaterEqual(max(sheet.shape[0], sheet.shape[1]), 400)
        self.assertEqual(renderer.content_scale, 5)
        self.assertTrue((sheet == 0).any())
        # Rectangular frame present on all four sides (AA may soften exact edge pixels)
        self.assertLess(int(np.min(sheet[0:3, sheet.shape[1] // 2, 0])), 40)
        self.assertLess(int(np.min(sheet[-3:, sheet.shape[1] // 2, 0])), 40)
        self.assertLess(int(np.min(sheet[sheet.shape[0] // 2, 0:3, 0])), 40)
        self.assertLess(int(np.min(sheet[sheet.shape[0] // 2, -3:, 0])), 40)


if __name__ == '__main__':
    unittest.main()
