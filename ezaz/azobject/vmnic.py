
from .azobject import AzRoActionable
from .azobject import AzSubObjectContainer


class VmNic(AzRoActionable, AzSubObjectContainer):
    @classmethod
    def azobject_name_list(cls):
        return ['vm', 'nic']

    @classmethod
    def get_cmd_base(cls):
        return ['vm', 'nic']

    @classmethod
    def get_parent_class(cls):
        from .vm import Vm
        return Vm

    @classmethod
    def get_child_classes(cls):
        from .vmipaddr import VmIpAddr
        return [VmIpAddr]

    @classmethod
    def get_self_id_argconfig_cmddest(cls, is_parent):
        return 'nic'

    def list_cache_infos(self, infolist):
        # Really horrible azure-cli behavior; list json is totally
        # different from show json.
        pass
