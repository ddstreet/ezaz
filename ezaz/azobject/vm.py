
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
            return (self.required_arg('image', opts, 'create') |
                    self.optional_flag_arg('no_wait', opts) |
                    {'--accept-term': None,
                     '--enable-secure-boot': None,
                     '--enable-vtpm': None})
        if cmdname == 'delete':
            return self.optional_flag_args(['yes', 'no_wait'], opts)
        return super()._get_cmd_args(cmdname, opts)
