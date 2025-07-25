
from .azobject import AzRoActionable
from .azobject import AzSubObjectContainer
from ..exception import NoPublicIp


class NicIpAddr(AzRoActionable, AzSubObjectContainer):
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
    def get_child_classes(cls):
        from .nicpublicip import NicPublicIp
        return [NicPublicIp]

    @classmethod
    def get_self_id_argconfig_cmddest(cls, is_parent):
        return 'name'

    def _get_public_ip_children(self):
        from .nicpublicip import NicPublicIp
        return self.get_children(NicPublicIp.azobject_name())

    def get_public_ip(self):
        for public_ip in self._get_public_ip_children():
            return public_ip
        raise NoPrimaryIpAddr(self)
