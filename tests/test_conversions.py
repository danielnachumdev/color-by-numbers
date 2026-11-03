import unittest

import numpy as np

from color_by_numbers.helpers import grayscale_to_rgb, rgb_to_grayscale


class TestConversions(unittest.TestCase):
    def test_rgb_to_grayscale_known_values(self):
        rgb = np.array([[[255, 0, 0], [0, 255, 0]], [[0, 0, 255], [255, 255, 255]]], dtype=np.uint8)
        gray = rgb_to_grayscale(rgb)
        self.assertEqual(gray.shape, (2, 2))
        self.assertEqual(int(gray[0, 0]), int(np.dot([255, 0, 0], [0.2989, 0.587, 0.114]).astype(np.uint8)))
        self.assertEqual(int(gray[1, 1]), int(np.dot([255, 255, 255], [0.2989, 0.587, 0.114]).astype(np.uint8)))

    def test_grayscale_to_rgb_replicates_channels(self):
        gray = np.array([[10, 20], [30, 40]], dtype=np.uint8)
        rgb = grayscale_to_rgb(gray)
        self.assertEqual(rgb.shape, (2, 2, 3))
        np.testing.assert_array_equal(rgb[:, :, 0], gray)
        np.testing.assert_array_equal(rgb[:, :, 1], gray)
        np.testing.assert_array_equal(rgb[:, :, 2], gray)
