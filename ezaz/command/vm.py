
import subprocess

from .. import LOGGER
from ..exception import NoPrimaryNic
from .command import AzObjectActionCommand


class VmCommand(AzObjectActionCommand):
    @classmethod
    def azclass(cls):
        from ..azobject.vm import Vm
        return Vm

    @classmethod
    def get_action_configs(cls):
        return [*super().get_action_configs(),
                cls.make_action_config('primary_ip_addr',
                                       description='Show virtual machine primary public ip address',
                                       argconfigs=cls.get_primary_ip_addr_action_config_argconfigs()),
                cls.make_action_config('ssh',
                                       description='Ssh to the virtual machine',
                                       argconfigs=cls.get_ssh_action_config_argconfigs())]

    @classmethod
    def get_primary_ip_addr_action_config_argconfigs(cls):
        return []

    @classmethod
    def get_ssh_action_config_argconfigs(cls):
        return []

    def primary_ip_addr(self, **opts):
        vm = self.azclass().get_instance(**opts)
        public_ip = vm.get_primary_nic().get_primary_ipaddr().get_public_ip()
        return public_ip.info().ipAddress

    def ssh(self, **opts):
        cmd = ['ssh', self.primary_ip_addr(**opts)]
        LOGGER.info(' '.join(cmd))
        return subprocess.run(cmd)
