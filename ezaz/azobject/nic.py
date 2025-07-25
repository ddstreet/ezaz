
from .azobject import AzRoActionable
from .azobject import AzSubObjectContainer
from ..exception import NoPrimaryIpAddr


class Nic(AzRoActionable, AzSubObjectContainer):
    @classmethod
    def azobject_name_list(cls):
        return ['nic']

    @classmethod
    def get_cmd_base(cls):
        return ['network', 'nic']

    @classmethod
    def get_parent_class(cls):
        from .resourcegroup import ResourceGroup
        return ResourceGroup

    @classmethod
    def get_child_classes(cls):
        from .nicipaddr import NicIpAddr
        return [NicIpAddr]

    @classmethod
    def get_self_id_argconfig_cmddest(cls, is_parent):
        return 'nic_name' if is_parent else 'name'

    def _get_ipaddr_children(self):
        from .nicipaddr import NicIpAddr
        return self.get_children(NicIpAddr.azobject_name())

    def get_primary_ipaddr(self):
        for ipaddr in self._get_ipaddr_children():
            if ipaddr.info().primary:
                return ipaddr
        raise NoPrimaryIpAddr(self)
