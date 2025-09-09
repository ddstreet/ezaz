
from .nicpublicip import NicPublicIp


class VmPublicIp(NicPublicIp):
    @classmethod
    def azobject_name_list(cls):
        return ['vm', 'public', 'ip', 'addr']

    @classmethod
    def get_parent_class(cls):
        from .vmipaddr import VmIpAddr
        return VmIpAddr

    @classmethod
    def get_azobject_id_argconfigs_noncmd_classes(cls):
        from .vm import Vm
        from .vmnic import VmNic
        from .vmipaddr import VmIpAddr
        return [Vm, VmNic, VmIpAddr]
