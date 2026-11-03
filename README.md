# color_by_numbers

**Photo → color-by-numbers** — turn RGB photos into posterized, paint-by-numbers style images with Lab-space luminance quantization (Gaussian blur + k-means).

Requires **Python 3.11+** (3.x with typing / `tuple[...]` syntax).

> **Status:** experimental research/script repo. Public API is small; expect churn. Not published to PyPI.

## Why color_by_numbers?

Full-color photos do not look like color-by-numbers sheets. This package reduces an image to a small set of luminance levels while keeping chrominance from Lab, so regions read as flat “paint cells” instead of continuous gradients.

- **`transform_image`** — Lab pipeline: blur L, quantize to `n_colors`, recombine with A/B, save RGB
- **`transform_image_rgb_individual_quantization`** — apply a custom per-channel mapping (experiments / alternate quantizers)
- Helpers for I/O, Lab↔RGB, Gaussian kernels, and several k-means / dumb quantizers
- **Clone-and-run** — `requirements.txt` + `main.py` demos (not a packaged CLI)

## Install

Clone and install dependencies (no PyPI package):

```bash
git clone https://github.com/danielnachumdev/color_by_numbers.git
cd color_by_numbers
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

## Quick start

```python
from color_by_numbers import transform_image

# Lab luminance quantization → color-by-numbers look
transform_image("input/photo.jpg", "output/photo_cbn.jpg", n_colors=5)
```

Per-channel RGB experiment (pass any channel callable):

```python
from color_by_numbers import transform_image_rgb_individual_quantization
from color_by_numbers.helpers import quantize_dumb

transform_image_rgb_individual_quantization(
    "input/photo.jpg",
    "output/photo_rgb_quant.jpg",
    lambda channel: quantize_dumb(channel, 5),
)
```

Demo entrypoint (expects `./input/img1.jpg`):

```bash
python main.py
```

## What you get

| Surface | Role |
| -------- | ---- |
| `transform_image` | Default Lab blur + k-means L quantization |
| `transform_image_rgb_individual_quantization` | Custom per-channel transforms |
| `color_by_numbers.helpers` | I/O, color spaces, kernels, quantizers |
| `main.py` | Local demos / timing experiments |
| `tests/` | unittest suite (kernels, I/O round-trips) |

## Contributing & development

Agent/developer workflow (layout, tests, PR labels): see [`AGENTS.md`](./AGENTS.md).

Report security issues privately via [GitHub advisories](https://github.com/danielnachumdev/color_by_numbers/security/advisories/new) — please do not open a public issue for vulnerabilities.
