import unittest
from pathlib import Path
from unittest.mock import Mock

import numpy as np

from color_by_numbers.loading.rgb_image_loader import RgbImageLoader


class TestRgbImageLoader(unittest.TestCase):
    def setUp(self) -> None:
        self.fixture = Path(__file__).parent / 'input' / 'colored_line.png'
        self.loader = RgbImageLoader()

    def test_load_from_path(self):
        rgb = self.loader.load_from_path(str(self.fixture))
        self.assertEqual(rgb.ndim, 3)
        self.assertEqual(rgb.shape[2], 3)

    def test_load_from_bytes(self):
        data = self.fixture.read_bytes()
        rgb = self.loader.load_from_bytes(data)
        self.assertTrue(np.array_equal(rgb, self.loader.load_from_path(str(self.fixture))))

    def test_load_from_url_uses_gateway(self):
        http = Mock()
        http.get.return_value = self.fixture.read_bytes()
        loader = RgbImageLoader(http=http)
        rgb = loader.load_from_url('https://example.com/photo.png')
        http.get.assert_called_once_with('https://example.com/photo.png')
        self.assertEqual(rgb.shape[2], 3)

    def test_rejects_non_http_url(self):
        with self.assertRaises(ValueError):
            self.loader.load_from_url('file:///tmp/photo.png')

    def test_rejects_empty_bytes(self):
        with self.assertRaises(ValueError):
            self.loader.load_from_bytes(b'')


if __name__ == '__main__':
    unittest.main()
