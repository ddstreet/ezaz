
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
    def get_cmd_base(cls, action):
        return ['sig', 'image-definition']

    def get_create_action_cmd_args(self, action, opts):
        return ArgMap(self.required_args_all(['offer', 'publisher', 'sku'], opts, 'create'),
                      self.optional_args(['os_type', 'architecture'], opts),
                      self._opts_to_args(hyper_v_generation='V2',
                                         features='SecurityType=TrustedLaunchSupported'))

    def get_create_action_cmd_args(self, action, opts):
        return self.optional_flag_arg('no_wait', opts)
