import unittest
from pathlib import Path

import numpy as np

from color_by_numbers.helpers import read_rgb, save_rgb, save_gray, read_gray, rgb_to_grayscale

_FIXTURES = Path(__file__).parent
_INPUT = _FIXTURES / 'input'
_OUTPUT = _FIXTURES / 'output'


class TestIO(unittest.TestCase):
    def test_rgb_with_gray(self):
        rgb = read_rgb(str(_INPUT / 'black_line.png'))
        save_rgb(str(_OUTPUT / 'black_line.png'), rgb)
        res = read_rgb(str(_OUTPUT / 'black_line.png'))
        self.assertTrue(np.array_equal(rgb, res))

    def test_rgb_with_rgb(self):
        rgb = read_rgb(str(_INPUT / 'colored_line.png'))
        save_rgb(str(_OUTPUT / 'colored_line.png'), rgb)
        res = read_rgb(str(_OUTPUT / 'colored_line.png'))
        self.assertTrue(np.array_equal(rgb, res))

    def test_gray_with_gray(self):
        gray = read_gray(str(_INPUT / 'black_line.png'))
        save_gray(str(_OUTPUT / 'black_line.png'), gray)
        res = read_gray(str(_OUTPUT / 'black_line.png'))
        self.assertTrue(np.array_equal(gray, res))

    def test_gray_with_rgb(self):
        gray = read_gray(str(_INPUT / 'colored_line.png'))
        save_gray(str(_OUTPUT / 'colored_line.png'), gray)
        res = read_gray(str(_OUTPUT / 'colored_line.png'))
        self.assertTrue(np.array_equal(gray, res))
