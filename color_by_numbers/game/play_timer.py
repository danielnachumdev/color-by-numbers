import time


class PlayTimer:
    def __init__(self) -> None:
        self._started: float | None = None
        self._accumulated = 0.0
        self._running = False
        self._fills = 0

    def reset(self) -> None:
        self._started = None
        self._accumulated = 0.0
        self._running = False
        self._fills = 0

    def start(self) -> None:
        if self._running:
            return
        self._started = time.perf_counter()
        self._running = True

    def stop(self) -> None:
        if not self._running or self._started is None:
            return
        self._accumulated += time.perf_counter() - self._started
        self._started = None
        self._running = False

    def record_fill(self) -> None:
        self.start()
        self._fills += 1

    def elapsed_seconds(self) -> float:
        total = self._accumulated
        if self._running and self._started is not None:
            total += time.perf_counter() - self._started
        return total

    def score(self, region_count: int) -> int:
        if region_count <= 0:
            return 0
        elapsed = max(1.0, self.elapsed_seconds())
        base = 1000 * region_count
        return max(0, int(base / elapsed) + self._fills * 5)

    def summary(self, region_count: int) -> str:
        seconds = int(self.elapsed_seconds())
        minutes = seconds // 60
        rem = seconds % 60
        return f'Time {minutes}:{rem:02d}  Score {self.score(region_count)}'
