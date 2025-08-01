
from ..argutil import ActionConfig
from ..exception import NoAzObjectExists
from .azobject import AzSubObject
from .azobject import AzShowable
from .azobject import AzListable


class Location(AzShowable, AzListable, AzSubObject):
    @classmethod
    def azobject_name_list(cls):
        return ['location']

    @classmethod
    def get_cmd_base(cls):
        return ['account']

    @classmethod
    def get_list_action_cmd(cls):
        return cls.get_cmd_base() + ['list-locations']

    @classmethod
    def get_subcmd_args_from_parent(cls, parent, cmdname, opts):
        # We don't want the --subscription param
        return {}

    def get_cmd_args(self, cmdname, opts):
        # We don't want the --location param
        return {}

    def _get_info(self, action, opts):
        for info in super()._get_info(action, opts):
            if info.name == self.azobject_id:
                return info
        raise NoAzObjectExists(self.azobject_text(), self.azobject_id)
