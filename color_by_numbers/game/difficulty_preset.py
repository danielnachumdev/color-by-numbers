from dataclasses import dataclass


@dataclass(frozen=True)
class DifficultyPreset:
    name: str
    n_colors: int
    min_region_area: int | None


class DifficultyPresets:
    EASY = DifficultyPreset('Easy', n_colors=5, min_region_area=220)
    NORMAL = DifficultyPreset('Normal', n_colors=8, min_region_area=None)
    HARD = DifficultyPreset('Hard', n_colors=12, min_region_area=80)

    @classmethod
    def all(cls) -> tuple[DifficultyPreset, ...]:
        return (cls.EASY, cls.NORMAL, cls.HARD)
