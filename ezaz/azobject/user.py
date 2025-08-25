
from .azobject import AzSubObject
from .azobject import AzListable
from .azobject import AzShowable


class User(AzShowable, AzListable, AzSubObject):
    @classmethod
    def azobject_name_list(cls):
        return ['user']

    @classmethod
    def info_id(cls, info):
        return info.id

    @classmethod
    def get_parent_class(cls):
        from .account import Account
        return Account

    @classmethod
    def get_cmd_base(cls):
        return ['ad']

    @classmethod
    def get_list_action_cmd(cls):
        return cls.get_cmd_base() + ['user', 'list']

    @classmethod
    def get_show_action_cmd(cls):
        return cls.get_cmd_base() + ['user', 'show']

    @classmethod
    def get_self_id_argconfig_cmddest(cls, is_parent):
        return 'id'

