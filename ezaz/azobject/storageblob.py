
from ..argutil import ChoicesArgConfig
from ..argutil import FlagArgConfig
from ..argutil import RequiredArgConfig
from ..argutil import ArgMap
from .azobject import AzCommonActionable
from .azobject import AzSubObject


class StorageBlob(AzCommonActionable, AzSubObject):
    @classmethod
    def azobject_name_list(cls):
        return ['storage', 'blob']

    @classmethod
    def azobject_cmd_arg(cls):
        return '--name'

    @classmethod
    def get_create_action_cmd(cls):
        return ['upload']

    @classmethod
    def get_create_action_argconfigs(cls):
        return [RequiredArgConfig('file', help='File to upload'),
                ChoicesArgConfig('type', choices=['append', 'block', 'page'], help='Type of blob to create'),
                FlagArgConfig('no_progress', help='Do not show upload progress bar')]

    @classmethod
    def get_delete_action_argconfigs(cls):
        return [RequiredArgConfig('file', help='File to download to'),
                FlagArgConfig('no_progress', help='Do not show download progress bar')]
