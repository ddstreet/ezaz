
from .command import AzObjectActionCommand


class StorageKeyCommand(AzObjectActionCommand):
    @classmethod
    def azclass(cls):
        from ..azobject.storagekey import StorageKey
        return StorageKey

    @property
    def _portal_url(self):
        # There is no page dedicated to each key, just the list of
        # keys, so we provide that
        urlpath = f'/resource{self.azobject.parent.info().id}'
        return f'{self._base_portal_url}{urlpath}/keys'

