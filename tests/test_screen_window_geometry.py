import unittest

from color_by_numbers.game.screen_window_geometry import ScreenWindowGeometry


class ScreenWindowGeometryTests(unittest.TestCase):
    def test_geometry_uses_fraction_and_centers(self) -> None:
        geometry = ScreenWindowGeometry(0.9, 0.9).geometry_string(1920, 1080)
        self.assertEqual(geometry, '1728x972+96+54')

    def test_geometry_clamps_to_screen(self) -> None:
        geometry = ScreenWindowGeometry(1.5, 1.5).geometry_string(800, 600)
        self.assertEqual(geometry, '800x600+0+0')


if __name__ == '__main__':
    unittest.main()
