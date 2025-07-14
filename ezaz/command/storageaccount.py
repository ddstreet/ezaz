
from .command import ResourceGroupSubCommand
from .command import StandardActionCommand


class StorageAccountCommand(ResourceGroupSubCommand, StandardActionCommand):
    ACTION_ARGUMENT_NAME = 'storage account'
    ACTION_ARGUMENT_METAVAR = 'ACCOUNT'
    ACTION_ATTR_NAME = 'storage_account'

    @classmethod
    def name(cls):
        return 'storageaccount'

    def _show(self, image_gallery):
        info = image_gallery.info
        msg = info.name
        if self.verbose:
            msg += f' (location: {info.location})'
        print(msg)

