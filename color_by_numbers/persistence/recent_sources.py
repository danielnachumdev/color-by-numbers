import json
from pathlib import Path


class RecentSources:
    def __init__(self, path: Path | None = None, limit: int = 12) -> None:
        self._path = path or (Path.home() / '.color_by_numbers' / 'recents.json')
        self._limit = limit

    def list(self) -> list[dict[str, str]]:
        if not self._path.exists():
            return []
        try:
            payload = json.loads(self._path.read_text(encoding='utf-8'))
        except (OSError, json.JSONDecodeError):
            return []
        if not isinstance(payload, list):
            return []
        return [item for item in payload if isinstance(item, dict) and 'kind' in item and 'value' in item]

    def remember(self, kind: str, value: str) -> None:
        entries = [item for item in self.list() if not (item.get('kind') == kind and item.get('value') == value)]
        entries.insert(0, {'kind': kind, 'value': value})
        self._path.parent.mkdir(parents=True, exist_ok=True)
        self._path.write_text(json.dumps(entries[: self._limit], indent=2), encoding='utf-8')
