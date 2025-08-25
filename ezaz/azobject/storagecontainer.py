
from contextlib import suppress

from ..argutil import ArgConfig
from ..argutil import ArgMap
from ..argutil import AzObjectArgConfig
from ..argutil import AzObjectDefaultId
from ..argutil import ChoicesArgConfig
from .azobject import AzCommonActionable
from .azobject import AzFilterer
from .azobject import AzSubObject
from .azobject import AzSubObjectContainer


class StorageContainer(AzCommonActionable, AzFilterer, AzSubObject, AzSubObjectContainer):
    @classmethod
    def azobject_name_list(cls):
        return ['storage', 'container']

    @classmethod
    def get_parent_class(cls):
        from .storageaccount import StorageAccount
        return StorageAccount

    @classmethod
    def get_child_classes(cls):
        from .storageblob import StorageBlob
        return [StorageBlob]

    @classmethod
    def get_self_id_argconfig_cmddest(cls, is_parent):
        return 'container_name' if is_parent else 'name'

    @classmethod
    def get_parent_common_argconfigs(self):
        return [*filter(lambda a: a.dest != 'resource_group', super().get_parent_common_argconfigs())]

    @classmethod
    def get_create_action_config(cls):
        return cls.make_action_config('create', az='stdout')

    @classmethod
    def get_common_argconfigs(cls, is_parent=False):
        from .storagekey import StorageKey
        return (super().get_common_argconfigs(is_parent=is_parent) +
                [ChoicesArgConfig('auth_mode',
                                  choices=['key', 'login'],
                                  default=cls.auth_mode,
                                  hidden=True),
                 AzObjectArgConfig('storage_key',
                                   cmddest='account_key',
                                   azclass=StorageKey,
                                   default=cls.storage_key,
                                   cmd_attr='value',
                                   hidden=True)])

    @classmethod
    def auth_mode(cls, **opts):
        parent = cls.get_parent_instance(**opts)
        return 'key' if parent.allow_shared_key_access else 'login'

    @classmethod
    def storage_key(cls, **opts):
        parent = cls.get_parent_instance(**opts)
        if not parent.allow_shared_key_access:
            return None

        from .storagekey import StorageKey
        name = StorageKey.azobject_name()

        with suppress(DefaultConfigNotFound):
            return parent.get_default_child(name).info().value

        with suppress(IndexError):
            return parent.get_children(name)[0].info().value

        raise NoAzObjectExists(name, 'any')
