import unittest

from color_by_numbers.game.canvas_view_transform import CanvasViewTransform


class CanvasViewTransformTests(unittest.TestCase):
    def test_fit_scale_uses_limiting_viewport_dimension(self) -> None:
        view = CanvasViewTransform()
        view.set_content_size(200, 100)
        view.set_viewport_size(400, 150)
        self.assertAlmostEqual(view.fit_scale(), 1.5)
        self.assertAlmostEqual(view.display_scale(), 1.5)

    def test_canvas_to_content_maps_centered_fit(self) -> None:
        view = CanvasViewTransform()
        view.set_content_size(100, 100)
        view.set_viewport_size(200, 200)
        # fit scale 2.0 → image fills viewport; origin at (0, 0)
        self.assertEqual(view.canvas_to_content(0, 0), (0, 0))
        self.assertEqual(view.canvas_to_content(199, 199), (99, 99))

    def test_canvas_to_content_rejects_outside_image(self) -> None:
        view = CanvasViewTransform()
        view.set_content_size(50, 50)
        view.set_viewport_size(200, 200)
        # fit scale 4 → 200x200 image; still fills. Use letterbox case:
        view.set_content_size(50, 50)
        view.set_viewport_size(300, 200)
        # fit = 4 → displayed 200x200, origin x=(300-200)/2=50
        self.assertIsNone(view.canvas_to_content(10, 100))
        self.assertEqual(view.canvas_to_content(50, 0), (0, 0))
        self.assertEqual(view.canvas_to_content(149, 100), (24, 25))

    def test_zoom_by_keeps_pivot_content_point(self) -> None:
        view = CanvasViewTransform()
        view.set_content_size(100, 100)
        view.set_viewport_size(200, 200)
        before = view.canvas_to_content(100, 100)
        view.zoom_by(2.0, 100, 100)
        after = view.canvas_to_content(100, 100)
        self.assertEqual(before, after)
        self.assertAlmostEqual(view.zoom(), 2.0)

    def test_pan_shifts_hit_testing(self) -> None:
        view = CanvasViewTransform()
        view.set_content_size(100, 100)
        view.set_viewport_size(200, 200)
        view.zoom_toward_center(2.0)
        mapped_before = view.canvas_to_content(100, 100)
        view.pan_by(20, 0)
        mapped_after = view.canvas_to_content(120, 100)
        self.assertEqual(mapped_before, mapped_after)

    def test_reset_restores_fit_zoom(self) -> None:
        view = CanvasViewTransform()
        view.set_content_size(100, 100)
        view.set_viewport_size(200, 200)
        view.zoom_toward_center(3.0)
        view.pan_by(10, 10)
        view.reset()
        self.assertAlmostEqual(view.zoom(), 1.0)
        self.assertEqual(view.canvas_to_content(0, 0), (0, 0))


if __name__ == '__main__':
    unittest.main()
