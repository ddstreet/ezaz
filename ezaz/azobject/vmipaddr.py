
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
    def get_azobject_id_argconfigs(cls, is_parent=False, **kwargs):
        from .vm import Vm
        from .vmnic import VmNic
        return [*[argconfig for argconfig in super().get_azobject_id_argconfigs(is_parent=is_parent, **kwargs)
                  if argconfig.dest not in ['vm', 'vm_nic']],
                *Vm.get_self_id_argconfigs(is_parent=True, noncmd=True),
                *VmNic.get_self_id_argconfigs(is_parent=True, cmddest='nic_name')]

    @classmethod
    def get_self_id_argconfig_cmddest(cls, is_parent):
        return 'name'
