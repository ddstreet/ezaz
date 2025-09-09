
from .nicipaddr import NicIpAddr


class VmIpAddr(NicIpAddr):
    @classmethod
    def azobject_name_list(cls):
        return ['vm', 'ip', 'addr']

    @classmethod
    def get_parent_class(cls):
        from .vmnic import VmNic
        return VmNic

    @classmethod
    def get_child_classes(cls):
        from .vmpublicip import VmPublicIp
        return [VmPublicIp]

    @classmethod
    def get_azobject_id_argconfigs_noncmd_classes(cls):
        from .vm import Vm
        return [Vm]

    @classmethod
    def get_azobject_id_argconfigs(cls, is_parent=False, **kwargs):
        argconfigs = super().get_azobject_id_argconfigs(is_parent=is_parent, **kwargs)
        if is_parent:
            return argconfigs

        from .vmnic import VmNic
        return [*[argconfig for argconfig in argconfigs if argconfig.dest not in ['vm_nic']],
                *VmNic.get_self_id_argconfigs(is_parent=True, cmddest='nic_name')]

    @classmethod
    def get_self_id_argconfig_cmddest(cls, is_parent):
        return 'name'

    def _get_public_ip_children(self):
        from .vmpublicip import VmPublicIp
        return self.get_children(VmPublicIp.azobject_name())
