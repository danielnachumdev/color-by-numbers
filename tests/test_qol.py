import tempfile
import unittest
from pathlib import Path

import numpy as np

from color_by_numbers.game.difficulty_preset import DifficultyPresets
from color_by_numbers.game.sheet_exporter import SheetExporter
from color_by_numbers.persistence.puzzle_session import PuzzleSession
from color_by_numbers.persistence.recent_sources import RecentSources
from color_by_numbers.puzzle.puzzle import Puzzle
from color_by_numbers.puzzle.puzzle_generator import PuzzleGenerator


class TestRecentSources(unittest.TestCase):
    def test_remember_dedupes_and_orders(self):
        with tempfile.TemporaryDirectory() as tmp:
            store = RecentSources(Path(tmp) / 'recents.json')
            store.remember('file', '/a.png')
            store.remember('url', 'https://example.com/x.jpg')
            store.remember('file', '/a.png')
            entries = store.list()
            self.assertEqual(entries[0]['value'], '/a.png')
            self.assertEqual(len(entries), 2)


class TestPuzzleSessionAndExport(unittest.TestCase):
    def _puzzle(self) -> Puzzle:
        image = np.zeros((40, 60, 3), dtype=np.uint8)
        image[:, :20] = (220, 40, 40)
        image[:, 20:40] = (40, 180, 40)
        image[:, 40:] = (40, 40, 220)
        return PuzzleGenerator().generate(image, n_colors=3, min_region_area=10, max_side=60)

    def test_session_round_trip(self):
        puzzle = self._puzzle()
        region_id = next(iter(puzzle.region_color_id))
        color_id = puzzle.region_color_id[region_id]
        x, y = puzzle.number_anchors[region_id]
        self.assertIsNotNone(puzzle.try_fill(x, y, color_id))
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / 'save.cbn.npz'
            PuzzleSession().save(path, puzzle, n_colors=3)
            loaded, n_colors = PuzzleSession().load(path)
            self.assertEqual(n_colors, 3)
            self.assertEqual(loaded.filled_regions, puzzle.filled_regions)
            self.assertEqual(len(loaded.boundary_paths), len(puzzle.boundary_paths))

    def test_export_png(self):
        puzzle = self._puzzle()
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / 'sheet.png'
            SheetExporter().export_png(path, puzzle)
            self.assertTrue(path.exists())
            self.assertGreater(path.stat().st_size, 0)


class TestDifficultyPresets(unittest.TestCase):
    def test_presets_exist(self):
        names = {preset.name for preset in DifficultyPresets.all()}
        self.assertEqual(names, {'Easy', 'Normal', 'Hard', 'Kids'})


class TestGenerationProgressCallback(unittest.TestCase):
    def test_progress_reports_increasing_fractions(self):
        image = np.zeros((48, 48, 3), dtype=np.uint8)
        image[:24, :] = (200, 30, 30)
        image[24:, :] = (30, 30, 200)
        seen: list[float] = []

        def on_progress(
            fraction: float,
            message: str,
            eta_seconds: float | None,
            elapsed: float,
        ) -> None:
            seen.append(fraction)
            self.assertTrue(message)
            self.assertGreaterEqual(fraction, 0.0)
            self.assertLessEqual(fraction, 1.0)
            self.assertGreaterEqual(elapsed, 0.0)

        PuzzleGenerator().generate(image, n_colors=2, max_side=48, progress=on_progress)
        self.assertGreaterEqual(len(seen), 5)
        self.assertLess(seen[-1], 1.0)
        self.assertGreaterEqual(seen[-1], 0.9)
        self.assertEqual(seen, sorted(seen))

    def test_download_progress_tracks_bytes_not_wall_clock(self):
        from color_by_numbers.puzzle.generation_progress import GenerationProgress

        tracker = GenerationProgress(include_download=True)
        first = tracker.set_download_progress(100_000, 1_000_000)[0]
        second = tracker.set_download_progress(500_000, 1_000_000)[0]
        third = tracker.set_download_progress(1_000_000, 1_000_000)[0]
        self.assertLess(first, 0.2)
        self.assertGreater(second, first)
        self.assertLess(third, 0.5)
        downloaded = tracker.complete_download()[0]
        decoded = tracker.complete_decode()[0]
        self.assertGreater(decoded, downloaded)
        self.assertLess(decoded, 0.6)
        finished = tracker.finish()[0]
        self.assertEqual(finished, 1.0)


if __name__ == '__main__':
    unittest.main()
