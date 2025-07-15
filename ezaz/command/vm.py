
from .command import Command


class VMCommand(Command):
    @classmethod
    def command_name_list(cls):
        return ['vm']

    def _run(self):
        print(f'{self.name()} running')
