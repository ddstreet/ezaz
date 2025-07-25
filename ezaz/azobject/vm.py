
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
    def get_action_configs(cls):
        return [*super().get_action_configs(),
                cls.make_action_config('log', description='Show vm serial console log'),
                cls.make_action_config('console', description='Access vm serial console'),
                cls.make_action_config('status', az='info', description='Get vm status'),
                cls.make_action_config('start', description='Start vm'),
                cls.make_action_config('restart', description='Restart vm'),
                cls.make_action_config('stop', description='Stop vm')]

    @classmethod
    def get_create_action_az(cls):
        return 'none'

    @classmethod
    def get_create_action_argconfigs(cls):
        from .imagegallery import ImageGallery
        from .imagedefinition import ImageDefinition
        from .imageversion import ImageVersion
        from .sku import Sku
        from .sshkey import SshKey
        from .storageaccount import StorageAccount
        return [*ImageGallery.get_self_id_argconfigs(is_parent=True, noncmd=True),
                *ImageDefinition.get_self_id_argconfigs(is_parent=True, noncmd=True),
                GroupArgConfig(ArgConfig('image',
                                         help='Deploy the provided full image id'),
                               AzObjectArgConfig('latest_image_version',
                                                 azclass=ImageDefinition,
                                                 cmdattr='id',
                                                 nodefault=True,
                                                 help='Deploy the latest version of this image definition'),
                               AzObjectArgConfig('image_version',
                                                 azclass=ImageVersion,
                                                 cmdattr='id',
                                                 nodefault=True,
                                                 help='Deploy this image version'),
                               ChoiceMapArgConfig('distro',
                                                  choicemap=DISTRO_IMAGES,
                                                  help='Deploy the specified distro'),
                               required=True,
                               cmddest='image'),
                AzObjectArgConfig('instance_type',
                                  azclass=Sku,
                                  dest='size',
                                  help=''),
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

    @classmethod
    def get_enable_boot_diagnostics_actioncfg(cls):
        # This isn't currently included in the user-facing actions;
        # it's invoked automatically by log/console if needed
        return cls.make_action_config('enable_boot_diagnostics', cmd=cls.get_cmd_base() + ['boot-diagnostics', 'enable'])

    def log_pre(self, opts):
        if not self.is_boot_diagnostics_enabled:
            self.enable_boot_diagnostics(**opts)
        return None

    def log(self, **opts):
        return self.do_action_config_instance_action('log', opts)

    def console_pre(self, opts):
        if not self.is_boot_diagnostics_enabled:
            self.enable_boot_diagnostics(**opts)
        return None

    def console(self, **opts):
        self.do_action_config_instance_action('console', opts)

    def status(self, **opts):
        return self.do_action_config_instance_action('status', opts)

    def start(self, **opts):
        self.do_action_config_instance_action('start', opts)

    def stop(self, **opts):
        self.do_action_config_instance_action('stop', opts)

    def restart(self, **opts):
        self.do_action_config_instance_action('restart', opts)

    def enable_boot_diagnostics(self, **opts):
        self.get_enable_boot_diagnostics_actioncfg().do_instance_action(self, self.get_self_id_opts(**opts))

    @property
    def is_boot_diagnostics_enabled(self):
        with suppress(AttributeError):
            return self.info().diagnosticsProfile.bootDiagnostics.enabled
        return False
