
from .command import SubCommand
from .resourcegroup import ResourceGroupCommand


class StorageAccountCommand(SubCommand):
    @classmethod
    def parent_command_cls(cls):
        return ResourceGroupCommand

    @classmethod
    def command_name_list(cls):
        return ['storage', 'account']

    def _show(self, image_gallery):
        info = image_gallery.info
        msg = info.name
        if self.verbose:
            msg += f' (location: {info.location})'
        print(msg)
