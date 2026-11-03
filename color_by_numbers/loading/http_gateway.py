from urllib.error import URLError
from urllib.request import Request, urlopen


class HttpGateway:
    def get(self, url: str, timeout: float = 30.0) -> bytes:
        request = Request(
            url,
            headers={'User-Agent': 'color-by-numbers/0.1'},
        )
        try:
            with urlopen(request, timeout=timeout) as response:
                return response.read()
        except URLError as exc:
            raise ConnectionError(f'Failed to download image: {exc.reason}') from exc
