from pathlib import Path
from tkinter import filedialog, messagebox, simpledialog

from ..webcam_preview import WebcamPreview
from .gallery_paths import GalleryPaths


class SourceActions:
    def __init__(self, host) -> None:
        self._host = host
        self._gallery = GalleryPaths()

    def open_image(self) -> None:
        path = filedialog.askopenfilename(
            title='Choose a photo',
            filetypes=[
                ('Images', '*.jpg *.jpeg *.png *.bmp *.webp'),
                ('All files', '*.*'),
            ],
        )
        if path:
            self.load_path(path)

    def open_gallery_folder(self) -> None:
        host = self._host
        folder = filedialog.askdirectory(title='Choose a photo folder')
        if not folder:
            return
        paths = self._gallery.list_images(folder)
        if not paths:
            messagebox.showinfo('Color by Numbers', 'No images found in that folder.')
            return
        labels = [Path(path).name for path in paths[:30]]
        choice = simpledialog.askstring(
            'Gallery',
            'Enter number:\n' + '\n'.join(f'{i + 1}. {label}' for i, label in enumerate(labels)),
            parent=host._root,
        )
        if not choice or not choice.isdigit():
            return
        index = int(choice) - 1
        if 0 <= index < len(paths):
            self.load_path(paths[index])

    def paste_clipboard(self) -> None:
        host = self._host
        try:
            rgb = host._clipboard.grab_rgb()
        except ValueError as exc:
            messagebox.showerror('Color by Numbers', str(exc))
            return
        host._source_kind = 'clipboard'
        host._source_value = 'clipboard'
        host._rgb = rgb
        host._loading_job.start_prepare_job(rgb=rgb)

    def capture_webcam(self) -> None:
        host = self._host
        try:
            rgb = WebcamPreview(host._root).choose_frame()
        except ValueError as exc:
            messagebox.showerror(host._strings.t('app_title'), str(exc))
            return
        if rgb is None:
            return
        host._source_kind = 'webcam'
        host._source_value = 'webcam'
        host._rgb = rgb
        host._loading_job.start_prepare_job(rgb=rgb)

    def load_path(self, path: str) -> None:
        host = self._host
        host._source_kind = 'file'
        host._source_value = path
        host._recents.remember('file', path)
        host._loading_job.start_prepare_job(path=path)

    def open_url(self) -> None:
        host = self._host
        url = simpledialog.askstring(
            'Open URL',
            'Image URL (http:// or https://):',
            parent=host._root,
        )
        if not url:
            return
        self.load_url(url)

    def load_url(self, url: str) -> None:
        host = self._host
        if host._prepare_job.is_running():
            messagebox.showinfo('Color by Numbers', 'Generation already running.')
            return
        host._source_kind = 'url'
        host._source_value = url
        host._recents.remember('url', url)
        host._loading_job.start_prepare_job(url=url)

    def open_recent(self) -> None:
        host = self._host
        entries = host._recents.list()
        if not entries:
            messagebox.showinfo('Color by Numbers', 'No recent images yet.')
            return
        labels = [f'{item["kind"]}: {item["value"]}' for item in entries]
        choice = simpledialog.askstring(
            'Recent',
            'Enter number:\n' + '\n'.join(f'{i + 1}. {label}' for i, label in enumerate(labels[:10])),
            parent=host._root,
        )
        if not choice or not choice.isdigit():
            return
        index = int(choice) - 1
        if index < 0 or index >= len(entries):
            return
        item = entries[index]
        if item['kind'] == 'file':
            self.load_path(item['value'])
        else:
            self.load_url(item['value'])

    def regenerate(self) -> None:
        host = self._host
        if host._rgb is None:
            messagebox.showinfo('Color by Numbers', 'Open an image or URL first.')
            return
        host._loading_job.start_prepare_job(rgb=host._rgb)
