
import subprocess

from .. import LOGGER
from ..argutil import ArgConfig
from ..argutil import BoolArgConfig
from ..argutil import DualExclusiveGroupArgConfig
from ..argutil import PositionalArgConfig
from ..exception import NoPrimaryNic
from ..exception import InvalidArgumentValue
from ..exception import RequiredArgument
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
                                       argconfigs=cls.get_ssh_action_config_argconfigs()),
                cls.make_action_config('scp',
                                       description='Scp file(s) to/from the virtual machine',
                                       argconfigs=cls.get_scp_action_config_argconfigs())]

    @classmethod
    def get_primary_ip_addr_action_config_argconfigs(cls):
        return []

    @classmethod
    def get_ssh_action_config_argconfigs(cls):
        return [*cls.azclass().get_azobject_id_argconfigs(),
                BoolArgConfig('check_host_key',
                              help='Allow ssh to verify remote host key; by default, we set ssh StrictHostKeyChecking=no')]

    @classmethod
    def get_scp_action_config_argconfigs(cls):
        return [*cls.get_ssh_action_config_argconfigs(),
                DualExclusiveGroupArgConfig('from',
                                            'to',
                                            dest='copy_to',
                                            default=True,
                                            help_a='Copy files from virtual machine',
                                            help_b='Copy files to virtual machine'),
                ArgConfig('dest',
                          help='For copy to, location on vm; for copy from, local location'),
                PositionalArgConfig('files',
                                    multiple=True,
                                    help='Files to copy to/from virtual machine')]

    def primary_ip_addr(self, **opts):
        vm = self.azclass().get_instance(**opts)
        public_ip = vm.get_primary_nic().get_primary_ipaddr().get_public_ip()
        return public_ip.info().ipAddress

    def ssh(self, check_host_key=False, **opts):
        cmd = ['ssh', self.primary_ip_addr(**opts)]
        if not check_host_key:
            cmd += ['-o', 'StrictHostKeyChecking=no', '-o', 'UserKnownHostsFile=/dev/null']
        return self._run_cmd(cmd)

    def scp(self, files, copy_to=True, dest=None, check_host_key=False, **opts):
        if not files:
            raise RequiredArgument('files', 'scp')
        if not isinstance(files, list) or not all((isinstance(f, str) for f in files)):
            raise InvalidArgumentValue('files', files)
        cmd = ['scp']
        if not check_host_key:
            cmd += ['-o', 'StrictHostKeyChecking=no', '-o', 'UserKnownHostsFile=/dev/null']
        ipaddr = self.primary_ip_addr(**opts)
        if copy_to:
            cmd += files
            cmd += [f'{ipaddr}:{dest or ""}']
        else:
            cmd += [f'{ipaddr}:{f}' for f in files]
            cmd += dest or '.'
        return self._run_cmd(cmd)

    def _run_cmd(self, cmd):
        cmdstr = ' '.join(cmd)
        if self.dry_run:
            LOGGER.warning(f"DRY-RUN (not running): {cmdstr}")
        else:
            LOGGER.info(cmdstr)
            return subprocess.run(cmd).returncode
