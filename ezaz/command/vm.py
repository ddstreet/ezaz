
from .command import AllActionCommand
from .resourcegroup import ResourceGroupCommand


class VMCommand(AllActionCommand):
    @classmethod
    def parent_command_cls(cls):
        return ResourceGroupCommand

    @classmethod
    def command_name_list(cls):
        return ['vm']

    @classmethod
    def parser_add_action_arguments(cls, group):
        super().parser_add_action_arguments(group)
        cls.parser_add_action_argument_console(group)
        cls.parser_add_action_argument_log(group)
        cls.parser_add_action_argument_restart(group)
        cls.parser_add_action_argument_start(group)
        cls.parser_add_action_argument_stop(group)

    @classmethod
    def parser_add_action_argument_console(cls, group):
        cls._parser_add_action_argument(group, '--console',
                                        help=f'Connect to the serial console.')

    @classmethod
    def parser_add_action_argument_log(cls, group):
        cls._parser_add_action_argument(group, '--log',
                                        help=f'Show the serial console log.')

    @classmethod
    def parser_add_action_argument_restart(cls, group):
        cls._parser_add_action_argument(group, '--restart',
                                        help=f'Restart the VM.')

    @classmethod
    def parser_add_action_argument_start(cls, group):
        cls._parser_add_action_argument(group, '--start',
                                        help=f'Start the VM.')

    @classmethod
    def parser_add_action_argument_stop(cls, group):
        cls._parser_add_action_argument(group, '--stop',
                                        help=f'Stop the VM.')

    def console(self):
        print('im a console!')

    def log(self):
        print('the log tastes like burnding!')

    def restart(self):
        print('go restart!')

    def start(self):
        print('start me up')

    def stop(self):
        print('stop in the name of the vm')
