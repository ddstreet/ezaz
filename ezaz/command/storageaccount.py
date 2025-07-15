
from .command import DefineSubCommand
from .resourcegroup import ResourceGroupSubCommand


class StorageAccountCommand(ResourceGroupSubCommand):
    @classmethod
    def command_name_list(cls):
        return ['storage', 'account']

    def _show(self, image_gallery):
        info = image_gallery.info
        msg = info.name
        if self.verbose:
            msg += f' (location: {info.location})'
        print(msg)


StorageAccountSubCommand = DefineSubCommand(ResourceGroupSubCommand, StorageAccountCommand)
