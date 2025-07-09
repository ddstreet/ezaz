
from .command import Command


class VMCommand(Command):
    @classmethod
    def name(cls):
        return 'vm'

    def run(self):
        print(f'{self.name()} running')
