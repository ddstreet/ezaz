
from .command import AzObjectActionCommand


class StorageContainerCommand(AzObjectActionCommand):
    @classmethod
    def azclass(cls):
        from ..azobject.storagecontainer import StorageContainer
        return StorageContainer

    @property
    def _base_portal_url(self):
        return f'https://portal.azure.com/#view/Microsoft_Azure_Storage/ContainerMenuBlade/~/overview'

    @property
    def _portal_url(self):
        import urllib.parse
        storage_account_path = f'storageAccountId/{urllib.parse.quote_plus(self.azobject.parent.info().id)}'
        return f'{self._base_portal_url}/{storage_account_path}/path/{self.azobject.azobject_id}'
