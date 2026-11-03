class SettingsSnapshot:
    def build(
        self,
        *,
        geometry: str,
        paint_mode: bool,
        highlight: bool,
        edge_aware: bool,
        color_mode: str,
        preset: str,
        n_colors: int,
        paper: str,
        language: str,
    ) -> dict:
        return {
            'geometry': geometry,
            'paint_mode': paint_mode,
            'highlight': highlight,
            'edge_aware': edge_aware,
            'color_mode': color_mode,
            'preset': preset,
            'n_colors': n_colors,
            'paper': paper,
            'language': language,
        }
