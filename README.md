# color_by_numbers

**Photo → playable color-by-numbers** — open a photo, get classic outlines + region numbers + a numbered palette, and fill regions in a local game window.

Requires **Python 3.11+** with **tkinter** available (for the game window). On Debian/Ubuntu: `sudo apt install python3-tk` if your interpreter lacks it. Uses **[uv](https://docs.astral.sh/uv/)** for the environment.

> **Status:** playable local game (tkinter). Packaging as a standalone EXE is planned later; not on PyPI.

## Why color_by_numbers?

Full-color photos are not paint-by-numbers sheets. This app quantizes the photo to a small palette, builds contiguous paint regions, draws black outlines and numbers, and lets you fill each region with the matching palette color.

- **Game GUI** — open an image, choose color count, paint until complete
- **`Puzzle` / `PuzzleGenerator`** — library API for the same pipeline
- Legacy Lab posterize helpers (`transform_image*`) still available for experiments

## Install

```bash
git clone https://github.com/danielnachumdev/color_by_numbers.git
cd color_by_numbers
uv sync
```

## Quick start (game)

Any of these open the same GUI:

```bash
uv run color-by-numbers
uv run python -m color_by_numbers
uv run python main.py
```

1. Open a local image, URL, or **File → Recent…** (drag-and-drop if your Tk build supports it)  
2. Choose a difficulty **Preset** (Easy / Normal / Hard) or set **Colors**, then **New puzzle** (Cancel stops generation)  
3. Select a numbered swatch (remaining counts shown), then click matching regions  
4. Correct fills stick; wrong color is ignored. Finish all regions to win  

**Play QoL:** Undo/Redo (`Ctrl+Z` / `Ctrl+Y`), Hint (`H`), highlight current color, auto-advance when a color is done, clearer progress (`Color N: X left — filled/total (%)`), line thickness controls, toggle preview (`P`).

**View:** window ~90% of screen; wheel / `+` `-` zoom; `0` Fit; `1` 100%; arrows pan; middle-drag pan.

**File:** save/load progress (`.cbn.npz`), export sheet+palette as PNG/PDF.

Future standalone EXE will use the same entrypoint (`color_by_numbers.__main__:main`).

## Library usage

```python
from color_by_numbers import PuzzleGenerator
from color_by_numbers.helpers import read_rgb

rgb = read_rgb("input/photo.jpg")
puzzle = PuzzleGenerator().generate(rgb, n_colors=8)
print(puzzle.progress())  # (0, region_count)
puzzle.try_fill(x=10, y=12, palette_index=0)
```

Legacy posterize (experiment):

```python
from color_by_numbers import transform_image

transform_image("input/photo.jpg", "output/photo_cbn.jpg", n_colors=5)
```

## What you get

| Surface | Role |
| -------- | ------ |
| `uv run color-by-numbers` / `python -m color_by_numbers` / `main.py` | Playable tkinter game |
| `Puzzle`, `PuzzleGenerator`; `GameApp` via `color_by_numbers.game.game_app` | Public library API |
| `color_by_numbers.helpers` | I/O, color spaces, kernels, experiment quantizers |
| `transform_image*` | Legacy Lab / per-channel posterize helpers |
| `tests/` | unittest suite |

## Contributing & development

Agent/developer workflow (layout, tests, PR labels): see [`AGENTS.md`](./AGENTS.md).

```bash
uv sync --group dev
uv run pytest -q
```

Report security issues privately via [GitHub advisories](https://github.com/danielnachumdev/color_by_numbers/security/advisories/new) — please do not open a public issue for vulnerabilities.
