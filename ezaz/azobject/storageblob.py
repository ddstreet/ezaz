
from ..argutil import ArgMap
from .azobject import AzCommonActionable
from .azobject import AzDownloadable
from .azobject import AzSubObject


class StorageBlob(AzCommonActionable, AzDownloadable, AzSubObject):
    @classmethod
    def azobject_name_list(cls):
        return ['storage', 'blob']

    @classmethod
    def azobject_cmd_arg(cls):
        return '--name'

    @classmethod
    def get_create_action_cmd(cls, action):
        return ['upload']

    def get_create_action_cmd_args(self, action, opts):
        return ArgMap(self.required_arg('file', opts, 'create'),
                      self.optional_arg('type', opts),
                      self.optional_flag_arg('no_progress', opts))

    def get_delete_action_cmd_args(self, action, opts):
        return ArgMap(self.required_arg('file', opts, 'delete'),
                      self.optional_flag_arg('no_progress', opts))
