"""Playable color-by-numbers desktop app package."""

try:
    from .game_app import GameApp
except ModuleNotFoundError as exc:
    # CI images may lack system tkinter; keep helpers importable headless.
    missing = exc.name or ''
    if 'tkinter' not in missing and 'tkinter' not in str(exc):
        raise
else:
    __all__ = [
        'GameApp',
    ]
