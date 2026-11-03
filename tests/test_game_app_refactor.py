import time
import unittest
import unittest.mock
from pathlib import Path

from color_by_numbers.game.game_app.download_work_detail import DownloadWorkDetail
from color_by_numbers.game.game_app.prepare_job_title import PrepareJobTitle
from color_by_numbers.game.game_app.settings_snapshot import SettingsSnapshot
from color_by_numbers.game.game_app.gallery_paths import GalleryPaths


class TestDownloadWorkDetail(unittest.TestCase):
    def setUp(self) -> None:
        self.detail = DownloadWorkDetail()

    def test_format_bytes_units(self) -> None:
        self.assertEqual(self.detail.format_bytes(500), '500 B')
        self.assertEqual(self.detail.format_bytes(2048), '2.0 KB')
        self.assertEqual(self.detail.format_bytes(1024 * 1024), '1.0 MB')

    def test_work_detail_empty_when_not_download(self) -> None:
        self.assertEqual(
            self.detail.format_work_detail({'bytes': 10}, 'Quantizing…'),
            '',
        )

    def test_work_detail_waiting(self) -> None:
        text = self.detail.format_work_detail(
            {'bytes': 0, 'total': None, 'started': None},
            'Downloading…',
        )
        self.assertEqual(text, 'Waiting for first bytes…')

    def test_work_detail_with_total_and_speed(self) -> None:
        started = time.perf_counter() - 1.0
        text = self.detail.format_work_detail(
            {'bytes': 1024, 'total': 2048, 'started': started},
            'Download 50%',
        )
        self.assertIn('1.0 KB / 2.0 KB', text)
        self.assertIn('/s', text)


class TestPrepareJobTitle(unittest.TestCase):
    def test_titles(self) -> None:
        titles = PrepareJobTitle()
        self.assertEqual(titles.for_inputs(url='https://x'), 'Downloading image…')
        self.assertEqual(titles.for_inputs(path='/a.png'), 'Loading image…')
        self.assertEqual(titles.for_inputs(rgb=object()), 'Generating puzzle…')


class TestSettingsSnapshot(unittest.TestCase):
    def test_builds_expected_keys(self) -> None:
        snapshot = SettingsSnapshot().build(
            geometry='800x600',
            paint_mode=True,
            highlight=False,
            edge_aware=True,
            color_mode='Normal',
            preset='Kids',
            n_colors=6,
            paper='Letter',
            language='he',
        )
        self.assertEqual(
            set(snapshot),
            {
                'geometry',
                'paint_mode',
                'highlight',
                'edge_aware',
                'color_mode',
                'preset',
                'n_colors',
                'paper',
                'language',
            },
        )
        self.assertEqual(snapshot['n_colors'], 6)
        self.assertEqual(snapshot['paper'], 'Letter')


class TestGalleryPaths(unittest.TestCase):
    def test_lists_image_suffixes_sorted(self) -> None:
        with unittest.mock.patch.object(Path, 'iterdir') as mocked:
            mocked.return_value = [
                Path('/g/b.PNG'),
                Path('/g/notes.txt'),
                Path('/g/a.jpg'),
            ]
            paths = GalleryPaths().list_images('/g')
        self.assertEqual(paths, ['/g/a.jpg', '/g/b.PNG'])


class TestPrepareGenerateJob(unittest.TestCase):
    def test_start_runs_generator_and_reports_ready(self) -> None:
        import numpy as np

        from color_by_numbers.game.game_app.prepare_generate_job import PrepareGenerateJob

        rgb = np.zeros((8, 8, 3), dtype=np.uint8)
        fake_puzzle = object()

        class FakeLoader:
            pass

        class FakeGenerator:
            def generate(self, source, **kwargs):
                self.source = source
                return fake_puzzle

        job = PrepareGenerateJob(image_loader=FakeLoader(), generator=FakeGenerator())
        title = job.start(
            n_colors=2,
            min_region_area=1,
            preserve_detail=False,
            edge_aware=False,
            max_regions=None,
            skin_bias=False,
            locked_palette=None,
            on_rgb_loaded=lambda _rgb: None,
            rgb=rgb,
        )
        self.assertEqual(title, 'Generating puzzle…')
        job.thread.join(timeout=5)
        self.assertFalse(job.is_running())
        result = job.take_result()
        self.assertEqual(result['status'], 'ready')
        self.assertIs(result['puzzle'], fake_puzzle)


class TestGameAppPackageExport(unittest.TestCase):
    def test_game_app_module_exports_game_app_without_package_root_tk(self) -> None:
        import color_by_numbers
        import color_by_numbers.game as game_pkg

        self.assertFalse(hasattr(color_by_numbers, 'GameApp'))
        self.assertNotIn('GameApp', getattr(game_pkg, '__all__', []))
        # Avoid importing GameApp (pulls tkinter); assert export surface via source.
        init_path = Path(game_pkg.__file__).resolve().parent / 'game_app' / '__init__.py'
        source = init_path.read_text(encoding='utf-8')
        self.assertIn('from .game_app import GameApp', source)
        self.assertIn("'GameApp'", source)


if __name__ == '__main__':
    unittest.main()
