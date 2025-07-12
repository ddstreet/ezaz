

class SubConfig:
    def __init__(self, parent, config):
        self._parent = parent
        self._config = config

    def _save(self):
        self._parent._save()

    @property
    def verbose(self):
        return self._parent.verbose

    @property
    def dry_run(self):
        return self._parent.dry_run
