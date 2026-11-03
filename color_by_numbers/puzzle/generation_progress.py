import time
from collections import deque


class GenerationProgress:
    """Progress from concrete work units + recent throughput."""

    _DOWNLOAD_UNITS = 400
    _DECODE_UNITS = 50
    _GENERATE_UNITS = 450
    _UNKNOWN_DOWNLOAD_BIAS_BYTES = 1_500_000

    GENERATE_STAGES: tuple[tuple[str, int], ...] = (
        ('Resizing…', 40),
        ('Quantizing colors…', 160),
        ('Finding regions…', 70),
        ('Merging tiny regions…', 90),
        ('Building outlines…', 40),
        ('Smoothing borders…', 50),
    )

    def __init__(self, include_download: bool = False) -> None:
        self._include_download = include_download
        self._started = time.perf_counter()
        self._message = 'Downloading image…' if include_download else 'Starting…'
        self._download_bytes = 0
        self._download_total: int | None = None
        self._download_complete = not include_download
        self._decode_complete = not include_download
        self._generate_done = 0
        self._generate_total = sum(units for _name, units in self.GENERATE_STAGES)
        self._stage_index = -1
        self._stage_units = 0
        self._job_complete = False
        self._samples: deque[tuple[float, float]] = deque(maxlen=48)
        self._record_sample()

    def set_download_progress(self, downloaded: int, total: int | None) -> tuple[float, str, float | None, float]:
        self._message = 'Downloading image…'
        self._download_bytes = max(0, downloaded)
        if total is not None and total > 0:
            self._download_total = total
        return self.snapshot()

    def complete_download(self) -> tuple[float, str, float | None, float]:
        self._download_complete = True
        if self._download_total is None and self._download_bytes > 0:
            self._download_total = self._download_bytes
        self._message = 'Decoding image…'
        return self.snapshot()

    def complete_decode(self) -> tuple[float, str, float | None, float]:
        self._decode_complete = True
        self._message = 'Starting puzzle generation…'
        return self.snapshot()

    def begin_stage(self, message: str) -> tuple[float, str, float | None, float]:
        if self._stage_index >= 0:
            self._generate_done += self._stage_units
        self._stage_index += 1
        if self._stage_index < len(self.GENERATE_STAGES):
            expected, units = self.GENERATE_STAGES[self._stage_index]
            self._stage_units = units
            self._message = message or expected
        else:
            self._stage_units = 0
            self._message = message
        return self.snapshot()

    def pulse(self) -> tuple[float, str, float | None, float]:
        return self.snapshot()

    def finish_generate(self) -> tuple[float, str, float | None, float]:
        """Mark generation complete but keep the bar under 100% until the UI dismisses."""
        self._generate_done = self._generate_total
        self._stage_units = 0
        self._message = 'Applying puzzle to screen…'
        return self.snapshot()

    def finish(self) -> tuple[float, str, float | None, float]:
        """Only call this immediately before hiding the overlay."""
        self._download_complete = True
        self._decode_complete = True
        self._generate_done = self._generate_total
        self._stage_units = 0
        self._job_complete = True
        self._message = 'Ready'
        return self.snapshot()

    def snapshot(self) -> tuple[float, str, float | None, float]:
        units = self._units_done()
        self._record_sample(units)
        elapsed = time.perf_counter() - self._started
        return self._fraction(units), self._message, self._eta_seconds(units, elapsed), elapsed

    def _units_done(self) -> float:
        if self._job_complete:
            return self._units_total()
        download = self._download_units_done()
        decode = float(self._DECODE_UNITS) if self._decode_complete else 0.0
        generate = (self._generate_done / self._generate_total) * self._GENERATE_UNITS
        if not self._include_download:
            return decode + generate + self._DOWNLOAD_UNITS
        return download + decode + generate

    def _units_total(self) -> float:
        return float(self._DOWNLOAD_UNITS + self._DECODE_UNITS + self._GENERATE_UNITS)

    def _download_units_done(self) -> float:
        if not self._include_download:
            return float(self._DOWNLOAD_UNITS)
        if self._download_complete:
            return float(self._DOWNLOAD_UNITS)
        if self._download_total and self._download_total > 0:
            ratio = min(0.999, self._download_bytes / self._download_total)
            return ratio * self._DOWNLOAD_UNITS
        ratio = self._download_bytes / (self._download_bytes + self._UNKNOWN_DOWNLOAD_BIAS_BYTES)
        return min(0.92, ratio) * self._DOWNLOAD_UNITS

    def _fraction(self, units: float) -> float:
        fraction = max(0.0, min(1.0, units / self._units_total()))
        if not self._job_complete:
            return min(0.99, fraction)
        return fraction

    def _record_sample(self, units: float | None = None) -> None:
        value = self._units_done() if units is None else units
        self._samples.append((time.perf_counter(), value))

    def _eta_seconds(self, units: float, elapsed: float) -> float | None:
        if self._job_complete:
            return None
        remaining = self._units_total() - units
        if remaining <= 1e-6:
            return None
        if elapsed < 0.25 or len(self._samples) < 2:
            return None
        start_t, start_u = self._samples[0]
        end_t, end_u = self._samples[-1]
        if len(self._samples) >= 6:
            start_t, start_u = self._samples[-6]
        delta_t = end_t - start_t
        delta_u = end_u - start_u
        if delta_t < 0.2 or delta_u <= 1e-6:
            if units <= 1e-6:
                return None
            return max(0.5, remaining * elapsed / units)
        return max(0.5, remaining * delta_t / delta_u)
