
from ..argutil import ArgConfig
from ..argutil import ChoicesArgConfig
from ..argutil import FlagArgConfig
from ..argutil import ArgMap
from .azobject import AzCommonActionable
from .azobject import AzSubObject


class StorageBlob(AzCommonActionable, AzSubObject):
    @classmethod
    def azobject_name_list(cls):
        return ['storage', 'blob']

    @classmethod
    def get_parent_class(cls):
        from .storagecontainer import StorageContainer
        return StorageContainer

    @classmethod
    def get_create_action_cmd(cls):
        return cls.get_cmd_base() + ['upload']

    @classmethod
    def get_self_id_argconfig_dest(cls, is_parent):
        return 'name'

    @classmethod
    def get_create_action_argconfigs(cls):
        return [ArgConfig('f', 'file', required=True, help='File to upload'),
                ChoicesArgConfig('type', choices=['append', 'block', 'page'], help='Type of blob to create'),
                FlagArgConfig('no_progress', help='Do not show upload progress bar'),
                FlagArgConfig('overwrite', help='Overwrite an existing blob')]

    @classmethod
    def get_delete_action_argconfigs(cls):
        return [ArgConfig('f', 'file', required=True, help='File to download to'),
                FlagArgConfig('no_progress', help='Do not show download progress bar')]
