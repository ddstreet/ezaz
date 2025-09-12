
from .publicip import PublicIp


class NicPublicIp(PublicIp):
    @classmethod
    def azobject_name_list(cls):
        return ['nic', 'public', 'ip', 'addr']

    @classmethod
    def get_parent_class(cls):
        from .nicipaddr import NicIpAddr
        return NicIpAddr

    def id_list_supported(self, **opts):
        return False

    @classmethod
    def get_azobject_id_argconfigs_noncmd_classes(cls):
        from .nic import Nic
        from .nicipaddr import NicIpAddr
        return [Nic, NicIpAddr]

    def list_post(self, infolist, opts):
        # NicIpAddr only contain a single PublicIp (if any)
        try:
            public_ip_id = self.parent.info().publicIPAddress.id
            infolist = [info for info in infolist if info.id == public_ip_id]
        except AttributeError:
            infolist = []
        return super().list_post(infolist, opts)
