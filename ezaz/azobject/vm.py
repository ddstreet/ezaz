
import getpass

from contextlib import suppress

from .. import DISTRO_IMAGES
from ..argutil import ArgConfig
from ..argutil import ArgMap
from ..argutil import AzObjectArgConfig
from ..argutil import BoolArgConfig
from ..argutil import ChoiceMapArgConfig
from ..argutil import ChoicesArgConfig
from ..argutil import EnableDisableGroupArgConfig
from ..argutil import FlagArgConfig
from ..argutil import GroupArgConfig
from ..argutil import NoWaitBoolArgConfig
from ..argutil import NoWaitFlagArgConfig
from ..argutil import NumberArgConfig
from ..argutil import YesFlagArgConfig
from ..exception import InvalidArgumentValue
from ..exception import RequiredArgument
from .azobject import AzCommonActionable
from .azobject import AzSubObject


class VM(AzCommonActionable, AzSubObject):
    @classmethod
    def azobject_name_list(cls):
        return ['vm']

    @classmethod
    def get_parent_class(cls):
        from .resourcegroup import ResourceGroup
        return ResourceGroup

    @classmethod
    def get_self_id_argconfig_cmddest(cls, is_parent):
        return 'name'

    @classmethod
    def get_action_configmap(cls):
        return ArgMap(super().get_action_configmap(),
                      log=cls.make_action_config('log', az='stdout', description='Show vm serial console log'),
                      console=cls.make_action_config('console', description='Access vm serial console'),
                      status=cls.make_action_config('status', az='info', description='Get vm status'),
                      start=cls.make_action_config('start', description='Start vm'),
                      restart=cls.make_action_config('restart', description='Restart vm'),
                      stop=cls.make_action_config('stop', description='Stop vm'))

    @classmethod
    def get_create_action_argconfigs(cls):
        from .imageversion import ImageVersion
        from .sshkey import SshKey
        from .storageaccount import StorageAccount
        return [GroupArgConfig(AzObjectArgConfig('image', azclass=ImageVersion, help='The image id to deploy'),
                               ChoiceMapArgConfig('distro', choicemap=DISTRO_IMAGES, help='The distro to deploy'),
                               required=True,
                               cmddest='image'),
                ArgConfig('instance_type',
                          dest='size',
                          help='TODO'),
                ArgConfig('username',
                          dest='admin_username',
                          default=getpass.getuser(),
                          help='User to create on instance'),
                ArgConfig('password',
                          dest='admin_password',
                          help='User password'),
                AzObjectArgConfig('ssh-key',
                                  dest='ssh_key_name',
                                  azclass=SshKey,
                                  help='ssh key to use for authentication'),
                AzObjectArgConfig('boot-diagnostics-storage',
                                  azclass=StorageAccount,
                                  hidden=True),
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
                                dest='os_disk_size_gb',
                                help='Size of OS disk, in GB'),
                NoWaitFlagArgConfig()]

    @classmethod
    def get_delete_action_argconfigs(cls):
        return [BoolArgConfig('force',
                              dest='force_deletion',
                              help='Force deletion of the VM'),
                NoWaitBoolArgConfig(),
                YesFlagArgConfig()]

    @classmethod
    def get_log_action_cmd(cls):
        return cls.get_cmd_base() + ['boot-diagnostics', 'get-boot-log']

    @classmethod
    def get_console_action_cmd(cls):
        return ['serial-console', 'connect']

    @classmethod
    def get_status_action_cmd(cls):
        return cls.get_cmd_base() + ['get-instance-view']

    @classmethod
    def get_start_action_argconfigs(cls):
        return [NoWaitBoolArgConfig()]

    @classmethod
    def get_restart_action_argconfigs(cls):
        return [FlagArgConfig('force', help='Force restart of the VM by redeploying it'),
                NoWaitFlagArgConfig()]

    @classmethod
    def get_stop_action_argconfigs(cls):
        return [FlagArgConfig('force', dest='skip_shutdown', help='Force stop of the VM'),
                NoWaitFlagArgConfig()]

    def log(self, **opts):
        return self.get_action_config('log').do_instance_action(self, opts)

    def console(self, **opts):
        self.get_action_config('console').do_instance_action(self, opts)

    def status(self, **opts):
        return self.get_action_config('status').do_instance_action(self, opts)

    def start(self, **opts):
        self.get_action_config('start').do_instance_action(self, opts)

    def stop(self, **opts):
        self.get_action_config('stop').do_instance_action(self, opts)

    def restart(self, **opts):
        self.get_action_config('restart').do_instance_action(self, opts)
