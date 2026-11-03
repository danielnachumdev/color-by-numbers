class UiStrings:
    EN = {
        'app_title': 'Color by Numbers',
        'open_image': 'Open image…',
        'open_url': 'Open URL…',
        'paste': 'Paste',
        'webcam': 'Webcam',
        'new_puzzle': 'New puzzle',
        'cancel': 'Cancel',
        'undo': 'Undo',
        'redo': 'Redo',
        'hint': 'Hint',
        'complete': 'Puzzle complete!',
        'resume_autosave': 'Resume autosave slot {slot}?',
        'palette': 'Palette',
        'language': 'Language',
    }
    HE = {
        'app_title': 'צביעה לפי מספרים',
        'open_image': 'פתח תמונה…',
        'open_url': 'פתח קישור…',
        'paste': 'הדבק',
        'webcam': 'מצלמה',
        'new_puzzle': 'חידה חדשה',
        'cancel': 'ביטול',
        'undo': 'בטל',
        'redo': 'בצע שוב',
        'hint': 'רמז',
        'complete': 'החידה הושלמה!',
        'resume_autosave': 'להמשיך משבצת שמירה אוטומטית {slot}?',
        'palette': 'לוח צבעים',
        'language': 'שפה',
    }

    def __init__(self, language: str = 'en') -> None:
        self.set_language(language)

    def set_language(self, language: str) -> None:
        code = language.lower()
        self.language = 'he' if code.startswith('he') else 'en'
        self._table = self.HE if self.language == 'he' else self.EN

    @property
    def rtl(self) -> bool:
        return self.language == 'he'

    def t(self, key: str, **kwargs) -> str:
        template = self._table.get(key, self.EN.get(key, key))
        return template.format(**kwargs) if kwargs else template
