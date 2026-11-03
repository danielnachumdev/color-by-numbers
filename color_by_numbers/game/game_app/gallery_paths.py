from pathlib import Path


class GalleryPaths:
    _SUFFIXES = {'.jpg', '.jpeg', '.png', '.bmp', '.webp'}

    def list_images(self, folder: str) -> list[str]:
        return sorted(
            [
                str(path)
                for path in Path(folder).iterdir()
                if path.suffix.lower() in self._SUFFIXES
            ]
        )
