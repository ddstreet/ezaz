
from .command import ResourceGroupSubCommand


class StorageAccountCommand(ResourceGroupSubCommand):
    @classmethod
    def _cls_type_list(cls):
        return ['storage', 'account']

    def _show(self, image_gallery):
        info = image_gallery.info
        msg = info.name
        if self.verbose:
            msg += f' (location: {info.location})'
        print(msg)

