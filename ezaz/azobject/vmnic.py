
from .nic import Nic


class VmNic(Nic):
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

    def list_post(self, infolist, opts):
        # Really horrible azure-cli behavior; list json is totally
        # different from show json.
        infolist = [self.parent.get_child(self.azobject_name(), info._id).info()
                    for info in infolist]
        return super().list_post(infolist, opts)

    def _get_ipaddr_children(self):
        from .vmipaddr import VmIpAddr
        return self.get_children(VmIpAddr.azobject_name())
