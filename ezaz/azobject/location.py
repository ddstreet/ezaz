
from ..exception import NoAzObjectExists
from ..exception import NotCreatable
from ..exception import NotDeletable
from .azobject import AzSubObject


class Location(AzSubObject):
    @classmethod
    def azobject_name_list(cls):
        return ['location']

    @classmethod
    def get_cmd_base(cls, action):
        return ['account']

    @classmethod
    def get_list_action_cmd(cls, action):
        return ['list-locations']

    @classmethod
    def get_subcmd_args_from_parent(cls, parent, cmdname, opts):
        # We don't want the --subscription param
        return {}

    @classmethod
    def get_action_configmap(cls):
        return {}

    def get_cmd_args(self, cmdname, opts):
        # We don't want the --location param
        return {}

    def _get_info(self):
        for info in super()._get_info():
            if info.name == self.azobject_id:
                return info
        raise NoAzObjectExists(self.azobject_text(), self.azobject_id)
