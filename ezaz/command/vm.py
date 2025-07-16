
from .command import AllActionCommand
from .resourcegroup import ResourceGroupCommand


class VMCommand(AllActionCommand):
    @classmethod
    def parent_command_cls(cls):
        return ResourceGroupCommand

    @classmethod
    def command_name_list(cls):
        return ['vm']

    def _run(self):
        print(f'{self.name()} running')
