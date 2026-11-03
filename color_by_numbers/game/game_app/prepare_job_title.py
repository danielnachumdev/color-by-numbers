class PrepareJobTitle:
    def for_inputs(
        self,
        rgb=None,
        url: str | None = None,
        path: str | None = None,
    ) -> str:
        if url is not None:
            return 'Downloading image…'
        if path is not None:
            return 'Loading image…'
        return 'Generating puzzle…'
