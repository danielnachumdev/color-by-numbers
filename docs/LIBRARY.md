# Library API

Public imports from `color_by_numbers`:

| Name | Role |
| ---- | ---- |
| `Puzzle` | Playable puzzle state (fill / undo / progress) |
| `PuzzleGenerator` | Photo → puzzle pipeline |

## Generate a puzzle

```python
from color_by_numbers import PuzzleGenerator
from color_by_numbers.helpers import read_rgb

rgb = read_rgb("input/photo.jpg")
puzzle = PuzzleGenerator().generate(
    rgb,
    n_colors=8,
    edge_aware=True,
    preserve_detail=False,
)
print(puzzle.progress())
```

Optional `locked_palette` reuses an existing RGB palette (N×3 `uint8`) instead of clustering.

## Legacy posterize helpers

`transform_image` and `transform_image_rgb_individual_quantization` remain available for experiments but are **not** the game pipeline. Prefer `PuzzleGenerator` for product work.

```python
from color_by_numbers import transform_image

transform_image("input/photo.jpg", "output/photo_cbn.jpg", n_colors=5)
```

## Game UI

Import `GameApp` from `color_by_numbers.game.game_app` (keeps tkinter out of the package root for headless CI).
