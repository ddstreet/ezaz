
from contextlib import suppress

from .. import DISTRO_IMAGES
from ..argutil import ArgMap
from ..exception import InvalidArgumentValue
from ..exception import RequiredArgument
from .azobject import AzCommonActionable
from .azobject import AzSubObject


class VM(AzCommonActionable, AzSubObject):
    @classmethod
    def azobject_name_list(cls):
        return ['vm']

    @classmethod
    def azobject_cmd_arg(cls):
        return '--name'

    @classmethod
    def get_log_action_cmd(cls, action):
        return ['get-boot-log']

    @classmethod
    def get_console_action_cmd(cls, action):
        return []

    @classmethod
    def get_action_configmap(cls):
        return {}

    def get_create_action_cmd_args(self, action, opts):
        return ArgMap(self._image_arg(action, opts),
                      self._opts.to_args(boot_diagnostics_storage=self.storage_account),
                      self.optional_flag_arg('no_wait', opts),
                      self._opts_to_flag_args(accept_term=None,
                                              enable_secure_boot=None,
                                              enable_vtpm=None))

    def get_delete_action_cmd_args(self, action, opts):
        return self.optional_flag_args(['yes', 'no_wait'], opts)

    def get_start_action_cmd_args(self, action, opts):
        return self.optional_flag_arg('no_wait', opts)

    def get_restart_action_cmd_args(self, action, opts):
        return self.optional_flag_args(['force', 'no_wait'], opts)

    def get_stop_action_cmd_args(self, action, opts):
        return self.optional_flag_args(['skip-shutdown', 'no_wait'], opts)

    def _image_arg(self, action, opts):
        with suppress(RequiredArgument):
            return self.required_arg('image', opts, action)
        with suppress(RequiredArgument):
            distro = self.required_arg_value('distro', opts, action)
            with suppress(KeyError):
                return self._opts_to_args(image=DISTRO_IMAGES[distro])
            raise InvalidArgumentValue('distro', distro)
        raise RequiredArgumentGroup(['image', 'distro'], action, exclusive=True)

    @property
    def storage_account(self):
        # TODO: add param to specify storage account instead of default
        return self.parent.get_azsubobject_default_id(StorageAccount.azobject_name())
