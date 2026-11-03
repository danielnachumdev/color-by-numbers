import time


class DownloadWorkDetail:
    def format_work_detail(self, download_state: dict, message: str) -> str:
        if not message.startswith('Download'):
            return ''
        downloaded = int(download_state.get('bytes') or 0)
        total = download_state.get('total')
        started = download_state.get('started')
        speed = ''
        if started is not None:
            elapsed = max(0.001, time.perf_counter() - float(started))
            speed = f'  ·  {self.format_bytes(downloaded / elapsed)}/s'
        if isinstance(total, int) and total > 0:
            return f'{self.format_bytes(downloaded)} / {self.format_bytes(total)}{speed}'
        if downloaded > 0:
            return f'{self.format_bytes(downloaded)} downloaded{speed}'
        return 'Waiting for first bytes…'

    def format_bytes(self, size: float) -> str:
        units = ('B', 'KB', 'MB', 'GB')
        value = float(size)
        for unit in units:
            if value < 1024.0 or unit == units[-1]:
                if unit == 'B':
                    return f'{int(value)} {unit}'
                return f'{value:.1f} {unit}'
            value /= 1024.0
        return f'{value:.1f} GB'
