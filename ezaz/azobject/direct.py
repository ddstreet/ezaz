
from .azobject import AzAction


class DirectAction(AzAction):
    def az(self, *args):
        return super().az(*args, dry_runnable=False)
