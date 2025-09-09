
from .azobject import AzRoActionable
from .azobject import AzSubObject


class NicIpAddr(AzRoActionable, AzSubObject):
    @classmethod
    def azobject_name_list(cls):
        return ['nic', 'ip', 'addr']

    @classmethod
    def get_cmd_base(cls):
        return ['network', 'nic', 'ip-config']

    @classmethod
    def get_parent_class(cls):
        from .nic import Nic
        return Nic

    @classmethod
    def get_self_id_argconfig_cmddest(cls, is_parent):
        return 'name'
