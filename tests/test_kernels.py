import numpy as np
import unittest

from color_by_numbers.helpers import apply_kernel


class TestApplyKernelFunction(unittest.TestCase):

    def test_apply_kernel_square_identity(self):
        # Test applying a square identity kernel (no change should occur)
        image = np.array([[1, 2, 3],
                          [4, 5, 6],
                          [7, 8, 9]])

        identity_kernel = np.array([[0, 0, 0],
                                    [0, 1, 0],
                                    [0, 0, 0]])

        result = apply_kernel(image, identity_kernel)
        np.testing.assert_array_equal(result, image)

    def test_apply_kernel_ones(self):
        # Test applying a kernel of all ones (blurring effect)
        image = np.array([[1, 2, 3],
                          [4, 5, 6],
                          [7, 8, 9]])

        ones_kernel = np.array([[1, 1, 1],
                                [1, 1, 1],
                                [1, 1, 1]])

        result = apply_kernel(image, ones_kernel)
        # convolve2d(..., mode='same', boundary='symm')
        expected_result = np.array([[21, 27, 33],
                                    [39, 45, 51],
                                    [57, 63, 69]])
        np.testing.assert_array_equal(result, expected_result)

    def test_apply_kernel_edge_detection(self):
        # Test applying an edge detection kernel
        image = np.array([[1, 2, 3],
                          [4, 5, 6],
                          [7, 8, 9]])

        edge_detection_kernel = np.array([[-1, -1, -1],
                                          [-1, 8, -1],
                                          [-1, -1, -1]])

        result = apply_kernel(image, edge_detection_kernel)
        # convolve2d(..., mode='same', boundary='symm')
        expected_result = np.array([[-12, -9, -6],
                                    [-3, 0, 3],
                                    [6, 9, 12]])
        np.testing.assert_array_equal(result, expected_result)
