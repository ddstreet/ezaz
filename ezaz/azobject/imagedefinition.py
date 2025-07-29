
from .azobject import AzCommonActionable
from .azobject import AzSubObject


class ImageDefinition(AzCommonActionable, AzSubObject):
    @classmethod
    def azobject_name_list(cls):
        return ['image', 'definition']

    @classmethod
    def azobject_cmd_arg(cls):
        return '--gallery-image-definition'

    @classmethod
    def get_base_cmd(cls):
        return ['sig', 'image-definition']

    def _get_cmd_args(self, cmdname, opts):
        if cmdname == 'create':
            return (self.required_args_all(['offer', 'publisher', 'sku'], opts, 'create') |
                    self.optional_args(['os_type', 'architecture'], opts) |
                    {'--hyper-v-generation': 'V2',
                     '--features': 'SecurityType=TrustedLaunchSupported'})
        if cmdname == 'delete':
            return self.optional_flag_arg('no_wait', opts)
        return super()._get_cmd_args(cmdname, opts)
