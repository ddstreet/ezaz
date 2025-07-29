
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
    def _get_cmd(cls, cmdname):
        if cmdname == 'create':
            return 'upload'
        return cmdname

    def _get_cmd_args(self, cmdname, opts):
        if cmdname == 'create':
            return ArgMap(self.required_arg('file', opts, 'create'),
                          self.optional_arg('type', opts),
                          self.optional_flag_arg('no_progress', opts))
        if cmdname == 'download':
            return ArgMap(self.required_arg('file', opts, 'delete'),
                          self.optional_flag_arg('no_progress', opts))
        return {}
