
from ..azobject.vm import VM
from .command import ActionParserConfig
from .command import AllActionCommand
from .resourcegroup import ResourceGroupCommand


class VMCommand(AllActionCommand):
    @classmethod
    def parent_command_cls(cls):
        return ResourceGroupCommand

    @classmethod
    def azobject_class(cls):
        return VM

    @classmethod
    def parser_get_action_parsers(cls):
        return (super().parser_get_action_parsers() +
                [ActionParserConfig('console', description='Attach to serial console'),
                 ActionParserConfig('log', description='Show serial console log'),
                 ActionParserConfig('restart', description='Restart the VM'),
                 ActionParserConfig('start', description='Start the VM'),
                 ActionParserConfig('stop', description='Stop the VM')])

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
