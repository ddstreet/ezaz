
from ..exception import NoAzObjectExists
from ..exception import NotCreatable
from ..exception import NotDeletable
from .azobject import AzSubObject


class Location(AzSubObject):
    @classmethod
    def azobject_name_list(cls):
        return ['location']

    @classmethod
    def get_base_cmd(cls):
        return ['account']

    @classmethod
    def _get_cmd(cls, cmdname):
        if cmdname == 'create':
            raise NotCreatable('location')
        if cmdname == 'delete':
            raise NotDeletable('location')
        return 'list-locations'

    @classmethod
    def get_subcmd_args_from_parent(cls, parent, cmdname, opts):
        # We don't want the --subscription param
        return {}

    def get_cmd_args(self, cmdname, opts):
        # We don't want the --location param
        return {}

    def _get_info(self):
        for info in super()._get_info():
            if info.name == self.azobject_id:
                return info
        raise NoAzObjectExists(self.azobject_text(), self.azobject_id)
