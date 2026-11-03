from collections.abc import Callable
from urllib.error import URLError
from urllib.request import Request, urlopen

DownloadProgress = Callable[[int, int | None], None]


class HttpGateway:
    _CHUNK_SIZE = 64 * 1024

    def get(
        self,
        url: str,
        timeout: float = 120.0,
        progress: DownloadProgress | None = None,
    ) -> bytes:
        request = Request(
            url,
            headers={'User-Agent': 'color-by-numbers/0.1'},
        )
        try:
            with urlopen(request, timeout=timeout) as response:
                total = self._content_length(response)
                chunks: list[bytes] = []
                downloaded = 0
                while True:
                    chunk = response.read(self._CHUNK_SIZE)
                    if not chunk:
                        break
                    chunks.append(chunk)
                    downloaded += len(chunk)
                    if progress is not None:
                        progress(downloaded, total)
                if progress is not None:
                    progress(downloaded, total if total is not None else downloaded)
                return b''.join(chunks)
        except URLError as exc:
            raise ConnectionError(f'Failed to download image: {exc.reason}') from exc

    def _content_length(self, response) -> int | None:
        length = getattr(response, 'length', None)
        if isinstance(length, int) and length > 0:
            return length
        header = response.headers.get('Content-Length')
        if header is None:
            return None
        try:
            value = int(header)
        except ValueError:
            return None
        return value if value > 0 else None
