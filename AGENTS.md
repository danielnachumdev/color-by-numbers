# color_by_numbers – Agent Context

Implementation guide for coding agents changing **color_by_numbers**. Product pitch and user-facing install: [`README.md`](README.md).

---

## Orientation

| Question | Answer |
| -------- | ------ |
| What is this? | Playable **color-by-numbers game**: photo → outlined numbered regions + palette; tkinter fill-to-win UI |
| Importable code | `color_by_numbers/` |
| Toolchain | `pip` + [`requirements.txt`](requirements.txt) (no `pyproject.toml` / uv yet) |
| Python | 3.11+ recommended (needs `tkinter` for the game; use a CPython build that includes it) |
| Tests | `tests/` — `unittest`; **never delete** |
| Publish | **Not on PyPI** — clone-only; EXE packaging planned later (same `__main__` entry) |
| Secrets | No API keys required; do not invent credential files |

```text
.
├── color_by_numbers/
│   ├── __init__.py           # GameApp, Puzzle, PuzzleGenerator, legacy transform_*
│   ├── __main__.py           # launches GameApp
│   ├── transforms.py         # legacy Lab / per-channel posterize helpers
│   ├── helpers.py            # I/O, Lab/RGB, kernels, experiment quantizers
│   ├── puzzle/               # Puzzle model + generator pipeline
│   └── game/                 # tkinter GameApp, canvas, palette
├── tests/
├── main.py                   # same GUI entry as __main__
├── requirements.txt
├── README.md
└── .gitignore
```

Shared CI/CD patterns (when wired): [`danielnachumdev/actions`](https://github.com/danielnachumdev/actions) (`@latest`). How to adopt: [`HOW-TO-USE.md`](https://github.com/danielnachumdev/actions/blob/v1/HOW-TO-USE.md).

---

## Develop

```bash
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

| Task | Command |
| ---- | ------- |
| Game | `python -m color_by_numbers` or `python main.py` |
| Import smoke | `python -c "from color_by_numbers import GameApp, PuzzleGenerator"` |
| Tests | `PYTHONPATH=. python -m unittest discover -s tests -v` |

I/O tests use paths like `./input/black_line.png` relative to **cwd** — run those from `tests/` so fixtures under `tests/input/` resolve (`cd tests && PYTHONPATH=.. python -m unittest discover -v`). Root `input/` / `output/` are for demos and are gitignored.

### Dependencies

- **Runtime (`requirements.txt`):** `numpy`, `scipy`, `opencv-python`, `scikit-learn`, `danielutils`, `Pillow`
- Prefer editing `requirements.txt` until/unless the repo migrates to `pyproject.toml` + uv.

---

## Code style & domain notes

- Follow the writing-python skill when adding/refactoring modules (class-first, SRP files, no stub shims).
- **Product path:** `PuzzleGenerator.generate` — Lab k-means palette → connected regions per color → min-area merge → outlines → number anchors → `Puzzle`.
- **Game:** strict fill — `Puzzle.try_fill` only accepts the region’s true palette index; completion reveals `preview`.
- **Public surface:** `GameApp`, `Puzzle`, `PuzzleGenerator`, plus legacy `transform_image` / `transform_image_rgb_individual_quantization`.
- Legacy **`transform_image`:** RGB → Lab → Gaussian blur on L → `quantize_image1` → Lab→RGB → save. Experiment only; not the game pipeline.
- Quantizer variants in `helpers.py` (`quantize_image1` / `2` / `3`, `quantize_dumb`) are experiment helpers — keep behavior stable or update tests/docs when changing them.
- Many helpers are wrapped with `@announce` (prints on call) — noisy by design for demos; do not strip casually without an intentional logging strategy.
- `.gitignore` ignores `*.png` — do not rely on new PNGs being committed unless gitignore is updated; existing fixtures under `tests/` are already tracked.

---

## PRs, CI, and releases

1. Branch off `main`; open a PR into `main`.
2. Attach **exactly one** semver label: `noBump` | `bumpPatch` | `bumpMinor` | `bumpMajor` (labels already exist on the repo).
3. When thin CI from [`danielnachumdev/actions`](https://github.com/danielnachumdev/actions) is present, prefer required checks **`CI / CI`** and **`Semver / Semver`**. Until then, still use the semver labels for consistency.
4. **No CD / PyPI** on this repo today — do not add a local `publish.py` / quickpub path unless packaging is intentionally adopted.
5. Dependabot PRs (once enabled) stay on `noBump`.
6. Change shared CI/semver behavior in **`danielnachumdev/actions`**, not by re-vendoring workflow guts here.

### Repo gates

- Expect `.github/CODEOWNERS` → `@danielnachumdev` when actions adoption merges.
- Prefer private vulnerability reporting via GitHub Security Advisories.

---

## Sensitive / ignored

Do not commit: `.venv/`, `venv/`, `__pycache__/`, root demo `input/` / `output/` blobs, API keys. Respect `.gitignore`. There is no `uv.lock` yet.
