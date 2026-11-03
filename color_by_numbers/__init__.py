from .puzzle.puzzle import Puzzle
from .puzzle.puzzle_generator import PuzzleGenerator
from .transforms import transform_image, transform_image_rgb_individual_quantization

__all__ = [
    'Puzzle',
    'PuzzleGenerator',
    # Legacy experiment helpers (not used by the game pipeline):
    'transform_image',
    'transform_image_rgb_individual_quantization',
]
