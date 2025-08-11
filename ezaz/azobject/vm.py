
import getpass

from contextlib import suppress

from .. import DISTRO_IMAGES
from ..argutil import ArgConfig
from ..argutil import ArgMap
from ..argutil import ChoiceMapArgConfig
from ..argutil import ChoicesArgConfig
from ..argutil import EnableDisableGroupArgConfig
from ..argutil import GroupArgConfig
from ..argutil import NoWaitFlagArgConfig
from ..argutil import NumberArgConfig
from ..argutil import YesFlagArgConfig
from ..exception import InvalidArgumentValue
from ..exception import RequiredArgument
from .azobject import AzCommonActionable
from .azobject import AzSubObject
from .completer import AzObjectCompleter
from .sshkey import SshKey


class VM(AzCommonActionable, AzSubObject):
    @classmethod
    def azobject_name_list(cls):
        return ['vm']

    @classmethod
    def get_parent_class(cls):
        from .resourcegroup import ResourceGroup
        return ResourceGroup

    @classmethod
    def get_log_action_cmd(cls, action):
        return ['get-boot-log']

    @classmethod
    def get_self_id_argconfig_dest(cls, is_parent):
        return 'name'

    @classmethod
    def get_create_action_argconfigs(cls):
        return [GroupArgConfig(ArgConfig('image',
                                         help='The image id to deploy'),
                               ChoiceMapArgConfig('distro',
                                                  choicemap=DISTRO_IMAGES,
                                                  help='The distro to deploy'),
                               required=True,
                               dest='image'),
                ArgConfig('instance_type',
                          dest='size',
                          help='TODO - implement completion for this!'),
                ArgConfig('username',
                          dest='admin_username',
                          default=getpass.getuser(),
                          help='User to create on instance'),
                ArgConfig('password',
                          dest='admin_password',
                          help='User password'),
                ArgConfig('ssh-key',
                          completer=AzObjectCompleter(SshKey),
                          help='TODO - implement completion for this!'),
                ChoicesArgConfig('security_type',
                                 choices=['Standard', 'TrustedLaunch', 'ConfidentialVM'],
                                 default='TrustedLaunch',
                                 help='Security type'),
                EnableDisableGroupArgConfig('enable_secure_boot',
                                            default=True,
                                            help_enable='Enable secure boot (default)',
                                            help_disable='Disable secure boot'),
                EnableDisableGroupArgConfig('enable_vtpm',
                                            default=True,
                                            help_enable='Enable secure boot (default)',
                                            help_disable='Disable secure boot'),
                ChoicesArgConfig('os_type',
                                 choices=['linux', 'windows'],
                                 help='Type of OS'),
                NumberArgConfig('size',
                                help='Size of OS disk, in GB'),
                NoWaitFlagArgConfig()]

    @classmethod
    def get_delete_action_argconfigs(cls):
        return [NoWaitFlagArgConfig(), YesFlagArgConfig()]

    #def get_create_action_cmd_args(self, opts):
        #self._opts.to_args(boot_diagnostics_storage=self.storage_account),
        #self._opts_to_flag_args(accept_term=None,
        #                                      enable_secure_boot=None,
        #                                      enable_vtpm=None))

    @classmethod
    def get_start_action_argconfigs(cls):
        return [NoWaitFlagArgConfig()]

    @classmethod
    def get_restart_action_argconfigs(cls):
        return [FlagArgConfig('force', help='Force-restart'),
                NoWaitFlagArgConfig()]

    @classmethod
    def get_stop_action_argconfigs(cls):
        return [FlagArgConfig('force', dest='skip_shutdown', help='Force-stop'),
                NoWaitFlagArgConfig()]

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
        return self.parent.get_default_child_id(StorageAccount.azobject_name())
