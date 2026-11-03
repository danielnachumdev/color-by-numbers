from dataclasses import dataclass


@dataclass(frozen=True)
class DifficultyPreset:
    name: str
    n_colors: int
    min_region_area: int | None
    preserve_detail: bool = False
    kids_mode: bool = False
    max_regions: int | None = None
    skin_bias: bool = True


class DifficultyPresets:
    EASY = DifficultyPreset('Easy', n_colors=5, min_region_area=220, max_regions=80)
    NORMAL = DifficultyPreset('Normal', n_colors=8, min_region_area=None, max_regions=140)
    HARD = DifficultyPreset(
        'Hard', n_colors=12, min_region_area=80, preserve_detail=True, max_regions=220
    )
    KIDS = DifficultyPreset(
        'Kids', n_colors=4, min_region_area=280, kids_mode=True, max_regions=36
    )

    @classmethod
    def all(cls) -> tuple[DifficultyPreset, ...]:
        return (cls.EASY, cls.NORMAL, cls.HARD, cls.KIDS)
