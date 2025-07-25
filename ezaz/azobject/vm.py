
from .azobject import AzSubObject


class VM(AzSubObject):
    @classmethod
    def azobject_name_list(cls):
        return ['vm']

    @classmethod
    def azobject_cmd_arg(cls):
        return '--name'

    def _get_cmd_args(self, cmdname, opts):
        if cmdname == 'create':
            args = {'--accept-term': None,
                    '--enable-secure-boot': None,
                    '--enable-vtpm': None}
            return self._merge_cmd_args(self.required_arg('image', opts, 'create'), args)
        return {}
