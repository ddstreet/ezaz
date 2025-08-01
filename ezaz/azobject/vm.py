
from contextlib import suppress

from .. import DISTRO_IMAGES
from ..argutil import ArgConfig
from ..argutil import ArgMap
from ..argutil import ChoicesArgConfig
from ..argutil import FlagArgConfig
from ..argutil import RequiredGroupArgConfig
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
    def get_create_action_argconfigs(cls):
        return [RequiredGroupArgConfig(ArgConfig('image', help='The image id to deploy'),
                                       ChoicesArgConfig('distro', help='The distro to deploy', choices=DISTRO_IMAGES.keys())),
                FlagArgConfig('no_wait', help='Do not wait for long-running tasks to finish')]

    @classmethod
    def get_delete_action_argconfigs(cls):
        return [FlagArgConfig('no_wait', help='Do not wait for long-running tasks to finish'),
                FlagArgConfig('y', 'yes', help='Do not prompt for confirmation')]

    #def get_create_action_cmd_args(self, action, opts):
        #self._opts.to_args(boot_diagnostics_storage=self.storage_account),
        #self._opts_to_flag_args(accept_term=None,
        #                                      enable_secure_boot=None,
        #                                      enable_vtpm=None))

    @classmethod
    def get_start_action_argconfigs(cls):
        return [FlagArgConfig('no_wait', help='Do not wait for long-running tasks to finish')]

    @classmethod
    def get_restart_action_argconfigs(cls):
        return [FlagArgConfig('force', help='Force-restart'),
                FlagArgConfig('no_wait', help='Do not wait for long-running tasks to finish')]

    @classmethod
    def get_stop_action_argconfigs(cls):
        return [FlagArgConfig('skip_shutdown', help='Force-stop'),
                FlagArgConfig('no_wait', help='Do not wait for long-running tasks to finish')]

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
