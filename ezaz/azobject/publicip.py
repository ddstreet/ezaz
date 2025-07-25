
from .azobject import AzRoActionable
from .azobject import AzSubObject


class PublicIp(AzRoActionable, AzSubObject):
    @classmethod
    def azobject_name_list(cls):
        return ['public', 'ip', 'addr']

    @classmethod
    def get_cmd_base(cls):
        return ['network', 'public-ip']

    @classmethod
    def get_parent_class(cls):
        from .resourcegroup import ResourceGroup
        return ResourceGroup

    @classmethod
    def get_self_id_argconfig_cmddest(cls, is_parent):
        return 'name'
