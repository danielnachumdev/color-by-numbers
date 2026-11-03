# color_by_numbers – Agent Context

Implementation guide for coding agents changing **color_by_numbers**. Product pitch and user-facing install: [`README.md`](README.md).

---

## Orientation

| Question | Answer |
| -------- | ------ |
| What is this? | Python toolkit: photo → **color-by-numbers** style images (Lab L quantization) |
| Importable code | `color_by_numbers/` |
| Toolchain | `pip` + [`requirements.txt`](requirements.txt) (no `pyproject.toml` / uv yet) |
| Python | 3.11+ recommended (`tuple[...]` / modern typing in helpers) |
| Tests | `tests/` — `unittest`; **never delete** |
| Publish | **Not on PyPI** — clone-only; no CD wheel publish on `main` today |
| Secrets | No API keys required; do not invent credential files |

```text
.
├── color_by_numbers/    # Importable package
│   ├── __init__.py      # Re-exports from __main__
│   ├── __main__.py      # transform_image* APIs
│   └── helpers.py       # I/O, Lab/RGB, kernels, quantizers
├── tests/               # unittest + PNG fixtures under tests/input|output
├── main.py              # Local demos (expects ./input, writes ./output)
├── requirements.txt
├── README.md            # Marketing / user docs
└── .gitignore           # ignores root input/, output/, *.png, caches
```

Shared CI/CD patterns (when wired): [`danielnachumdev/actions`](https://github.com/danielnachumdev/actions) (`@latest`). How to adopt: [`HOW-TO-USE.md`](https://github.com/danielnachumdev/actions/blob/v1/HOW-TO-USE.md). Thin `.github/` adoption may land via a separate PR — do not assume workflows exist on `main` until they do.

---

## Develop

```bash
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

| Task | Command |
| ---- | ------- |
| Import smoke | `python -c "from color_by_numbers import transform_image"` |
| Tests | `cd tests && python -m unittest discover -v` |
| Demo | put a photo at `./input/img1.jpg`, then `python main.py` |

I/O tests use paths like `./input/black_line.png` relative to **cwd** — run unittest from `tests/` so fixtures under `tests/input/` resolve. Root `input/` / `output/` are for demos and are gitignored.

### Dependencies

- **Runtime (`requirements.txt`):** `numpy`, `scipy`, `opencv-python`, `scikit-learn`, `danielutils`
- Prefer editing `requirements.txt` until/unless the repo migrates to `pyproject.toml` + uv.

---

## Code style & domain notes

- Follow the writing-python skill when adding/refactoring modules (class-first, SRP files, no stub shims).
- Public surface today: `transform_image`, `transform_image_rgb_individual_quantization` (re-exported via `color_by_numbers/__init__.py` → `__main__.py`). Broader helpers live in `helpers.py` and are exported via `helpers.__all__`.
- **`transform_image`:** RGB → Lab → Gaussian blur on L (`gaussian_kernel(31, 5)`) → `quantize_image1` → Lab→RGB → save. Chrominance (A/B) is kept; only L is quantized.
- Quantizer variants (`quantize_image1` / `2` / `3`, `quantize_dumb`) are experiment helpers — keep behavior stable or update tests/docs when changing them.
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
