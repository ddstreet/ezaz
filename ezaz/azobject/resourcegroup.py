
from ..argutil import ArgConfig
from ..argutil import ArgMap
from ..argutil import AzObjectArgConfig
from ..argutil import BoolArgConfig
from ..argutil import BoolGroupArgConfig
from ..argutil import NoWaitFlagArgConfig
from ..argutil import YesFlagArgConfig
from .azobject import AzCommonActionable
from .azobject import AzSubObjectContainer


class ResourceGroup(AzCommonActionable, AzSubObjectContainer):
    @classmethod
    def azobject_name_list(cls):
        return ['resource', 'group']

    @classmethod
    def get_parent_class(cls):
        from .subscription import Subscription
        return Subscription

    @classmethod
    def get_child_classes(cls):
        from .imagegallery import ImageGallery
        from .nic import Nic
        from .publicip import PublicIp
        from .sshkey import SshKey
        from .storageaccount import StorageAccount
        from .vm import Vm
        return [ImageGallery, Nic, PublicIp, SshKey, StorageAccount, Vm]

    @classmethod
    def get_cmd_base(cls):
        return ['group']

    @classmethod
    def get_action_configs(cls):
        return [*super().get_action_configs(),
                cls.make_action_config('deploy', description='Deploy a template')]

    @classmethod
    def get_create_action_argconfigs(cls):
        from .location import Location
        return [AzObjectArgConfig('location', azclass=Location, help='Location'),
                BoolArgConfig('no_rbac', noncmd=True, help='Do not add RBAC owner/contributor roles for the signed in user')]

    def create(self, no_rbac=False, **opts):
        super().create(**opts)
        if no_rbac:
            return

        # Add owner and contributor RBAC for the signed-in user
        roleassignment = self.parent.get_null_child('role_assignment')
        opts['resource_group'] = self.azobject_id
        roleassignment.create(role='Owner', **opts)
        roleassignment.create(role='Contributor', **opts)
        roleassignment.create(role='Storage Blob Data Owner', **opts)

    @classmethod
    def get_delete_action_argconfigs(cls):
        return [NoWaitFlagArgConfig(), YesFlagArgConfig()]

    @classmethod
    def get_deploy_action_cmd(cls):
        return ['deployment', 'group', 'create']

    @classmethod
    def get_deploy_action_argconfigs(cls):
        return [ArgConfig('template_file', required=True, help='Template to deploy'),
                ArgConfig('parameter_file', help='Parameters for deployment'),
                BoolGroupArgConfig('no_prompt',
                                   help_no='Do not prompt for missing parameters',
                                   help_yes='Prompt for missing parameters'),
                NoWaitFlagArgConfig()]

    def deploy(self, *, template_file, **opts):
        self.do_action_config_instance_action('deploy', ArgMap(template_file=template_file, **opts))
