import json
from pathlib import Path

import numpy as np

from ..puzzle.puzzle import Puzzle


class PuzzleSession:
    def save(self, path: str | Path, puzzle: Puzzle, n_colors: int) -> None:
        target = Path(path)
        target.parent.mkdir(parents=True, exist_ok=True)
        np.savez_compressed(
            target,
            label_map=puzzle.label_map,
            palette=puzzle.palette,
            outlines=puzzle.outlines,
            preview=puzzle.preview,
            region_ids=np.array(sorted(puzzle.region_color_id), dtype=np.int32),
            region_colors=np.array(
                [puzzle.region_color_id[region_id] for region_id in sorted(puzzle.region_color_id)],
                dtype=np.int32,
            ),
            filled_regions=np.array(sorted(puzzle.filled_regions), dtype=np.int32),
            undo=np.array(puzzle._undo_stack, dtype=np.int32),
            redo=np.array(puzzle._redo_stack, dtype=np.int32),
            n_colors=np.array([n_colors], dtype=np.int32),
        )
        meta = {
            'number_anchors': {str(k): list(v) for k, v in puzzle.number_anchors.items()},
            'boundary_path_count': len(puzzle.boundary_paths),
        }
        meta_path = target.with_suffix(target.suffix + '.meta.json')
        boundary_path = target.with_suffix(target.suffix + '.boundaries.npz')
        meta_path.write_text(json.dumps(meta), encoding='utf-8')
        np.savez_compressed(
            boundary_path,
            **{f'path_{index}': points for index, points in enumerate(puzzle.boundary_paths)},
        )

    def load(self, path: str | Path) -> tuple[Puzzle, int]:
        target = Path(path)
        data = np.load(target, allow_pickle=False)
        region_color_id = {
            int(region_id): int(color_id)
            for region_id, color_id in zip(data['region_ids'], data['region_colors'])
        }
        meta = json.loads(target.with_suffix(target.suffix + '.meta.json').read_text(encoding='utf-8'))
        anchors = {int(k): (int(v[0]), int(v[1])) for k, v in meta['number_anchors'].items()}
        boundary_file = np.load(target.with_suffix(target.suffix + '.boundaries.npz'), allow_pickle=False)
        boundary_paths = [boundary_file[key] for key in sorted(boundary_file.files)]
        puzzle = Puzzle(
            label_map=data['label_map'],
            region_color_id=region_color_id,
            palette=data['palette'],
            outlines=data['outlines'],
            number_anchors=anchors,
            preview=data['preview'],
            boundary_paths=boundary_paths,
            filled_regions=set(int(v) for v in data['filled_regions'].tolist()),
        )
        puzzle._undo_stack = [int(v) for v in data['undo'].tolist()]
        puzzle._redo_stack = [int(v) for v in data['redo'].tolist()]
        n_colors = int(data['n_colors'][0])
        return puzzle, n_colors
