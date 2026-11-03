try:
    from tkinterdnd2 import DND_FILES
except ImportError:
    DND_FILES = None


class DragDropBinder:
    def enable(self, root, on_drop) -> None:
        if DND_FILES is None or not hasattr(root, 'drop_target_register'):
            return
        root.drop_target_register(DND_FILES)
        root.dnd_bind('<<Drop>>', on_drop)
