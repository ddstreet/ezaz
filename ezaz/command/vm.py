
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
                                       argconfigs=cls.get_scp_action_config_argconfigs()),
                cls.make_action_config('command',
                                       description='Run command on the virtual machine',
                                       argconfigs=cls.get_command_action_config_argconfigs())]

    @classmethod
    def get_primary_ip_addr_action_config_argconfigs(cls):
        return []

    @classmethod
    def get_secure_shell_action_common_config_argconfigs(cls):
        return [BoolArgConfig('check_host_key',
                              help='Allow ssh to verify remote host key; by default, we set ssh StrictHostKeyChecking=no'),
                ArgConfig('jump', 'J',
                          help='Use this ssh jump box')]

    @classmethod
    def get_ssh_action_config_argconfigs(cls):
        return [*cls.azclass().get_azobject_id_argconfigs(),
                *cls.get_secure_shell_action_common_config_argconfigs()]

    @classmethod
    def get_scp_action_config_argconfigs(cls):
        return [*cls.azclass().get_azobject_id_argconfigs(),
                *cls.get_secure_shell_action_common_config_argconfigs(),
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

    @classmethod
    def get_command_action_config_argconfigs(cls):
        return [*cls.azclass().get_azobject_id_argconfigs(),
                *cls.get_secure_shell_action_common_config_argconfigs(),
                PositionalArgConfig('commands',
                                    multiple=True,
                                    help='Command (and arguments) to run on virtual machine')]

    def primary_ip_addr(self, **opts):
        vm = self.azclass().get_instance(**opts)
        public_ip = vm.get_primary_nic().get_primary_ipaddr().get_public_ip()
        return public_ip.info().ipAddress

    def _get_secure_shell_common_params(self, check_host_key=False, jump=None, **opts):
        params = []
        if not check_host_key:
            params += ['-o', 'StrictHostKeyChecking=no', '-o', 'UserKnownHostsFile=/dev/null']
        if jump:
            params += ['-J', jump]
        return params

    def ssh(self, **opts):
        cmd = ['ssh'] + self._get_secure_shell_common_params(**opts) + [self.primary_ip_addr(**opts)]

        return self._run_cmd(cmd)

    def scp(self, files, copy_to=True, dest=None, **opts):
        if not files:
            raise RequiredArgument('files', 'scp')
        if not isinstance(files, list) or not all((isinstance(f, str) for f in files)):
            raise InvalidArgumentValue('files', files)

        cmd = ['scp'] + self._get_secure_shell_common_params(**opts)

        ipaddr = self.primary_ip_addr(**opts)
        if copy_to:
            cmd += files
            cmd += [f'{ipaddr}:{dest or ""}']
        else:
            cmd += [f'{ipaddr}:{f}' for f in files]
            cmd += dest or '.'

        return self._run_cmd(cmd)

    def command(self, commands, **opts):
        if not commands:
            raise RequiredArgument('commands', 'command')
        if not isinstance(commands, list) or not all((isinstance(c, str) for c in commands)):
            raise InvalidArgumentValue('commands', commands)

        cmd = ['ssh'] + self._get_secure_shell_common_params(**opts) + [self.primary_ip_addr(**opts)] + commands

        return self._run_cmd(cmd)

    def _run_cmd(self, cmd):
        cmdstr = ' '.join(cmd)
        if self.dry_run:
            LOGGER.warning(f"DRY-RUN (not running): {cmdstr}")
        else:
            LOGGER.info(cmdstr)
            return subprocess.run(cmd).returncode
