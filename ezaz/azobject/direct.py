
from . import AzAction


class DirectAction(AzAction):
    def __init__(self, verbose=False, dry_run=False):
        self._verbose = verbose
        self._dry_run = dry_run

    @property
    def verbose(self):
        return self._verbose

    @property
    def dry_run(self):
        return self._dry_run

    def az(self, *args):
        return super().az(*args, dry_runnable=False)
