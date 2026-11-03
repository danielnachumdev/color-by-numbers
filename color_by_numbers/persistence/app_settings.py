import json
from pathlib import Path


class AppSettings:
    def __init__(self, path: Path | None = None) -> None:
        self._path = path or (Path.home() / '.color_by_numbers' / 'settings.json')
        self._data = self._load()

    def get(self, key: str, default=None):
        return self._data.get(key, default)

    def set(self, key: str, value) -> None:
        self._data[key] = value
        self.save()

    def update(self, values: dict) -> None:
        self._data.update(values)
        self.save()

    def save(self) -> None:
        self._path.parent.mkdir(parents=True, exist_ok=True)
        self._path.write_text(json.dumps(self._data, indent=2), encoding='utf-8')

    def _load(self) -> dict:
        if not self._path.exists():
            return {}
        try:
            return json.loads(self._path.read_text(encoding='utf-8'))
        except (OSError, json.JSONDecodeError):
            return {}
