import json
from pathlib import Path

from ..puzzle.puzzle import Puzzle
from .puzzle_session import PuzzleSession


class AutosaveStore:
    def __init__(
        self,
        root: Path | None = None,
        sessions: PuzzleSession | None = None,
        slot_count: int = 3,
    ) -> None:
        self._root = root or (Path.home() / '.color_by_numbers' / 'autosave')
        self._sessions = sessions or PuzzleSession()
        self._slot_count = slot_count
        self._root.mkdir(parents=True, exist_ok=True)

    def save_slot(self, slot: int, puzzle: Puzzle, n_colors: int, label: str = '') -> Path:
        index = self._clamp_slot(slot)
        path = self._slot_path(index)
        self._sessions.save(path, puzzle, n_colors)
        meta = {'label': label, 'slot': index}
        path.with_suffix(path.suffix + '.slot.json').write_text(json.dumps(meta), encoding='utf-8')
        self._write_last(index)
        return path

    def load_slot(self, slot: int) -> tuple[Puzzle, int] | None:
        path = self._slot_path(self._clamp_slot(slot))
        if not path.exists():
            return None
        return self._sessions.load(path)

    def load_last(self) -> tuple[Puzzle, int, int] | None:
        last = self._read_last()
        if last is None:
            return None
        loaded = self.load_slot(last)
        if loaded is None:
            return None
        puzzle, n_colors = loaded
        return puzzle, n_colors, last

    def list_slots(self) -> list[dict]:
        entries: list[dict] = []
        for slot in range(1, self._slot_count + 1):
            path = self._slot_path(slot)
            label = ''
            meta_path = path.with_suffix(path.suffix + '.slot.json')
            if meta_path.exists():
                label = json.loads(meta_path.read_text(encoding='utf-8')).get('label', '')
            entries.append({'slot': slot, 'exists': path.exists(), 'label': label, 'path': str(path)})
        return entries

    def _slot_path(self, slot: int) -> Path:
        return self._root / f'slot_{slot}.cbn.npz'

    def _clamp_slot(self, slot: int) -> int:
        return max(1, min(self._slot_count, int(slot)))

    def _write_last(self, slot: int) -> None:
        (self._root / 'last.json').write_text(json.dumps({'slot': slot}), encoding='utf-8')

    def _read_last(self) -> int | None:
        path = self._root / 'last.json'
        if not path.exists():
            return None
        data = json.loads(path.read_text(encoding='utf-8'))
        slot = data.get('slot')
        return int(slot) if slot is not None else None
