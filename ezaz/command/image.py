
from .command import Command


class ImageCommand(Command):
    @classmethod
    def name(cls):
        return 'image'

    @classmethod
    def _parser_add_arguments(cls, parser):
        parser.add_argument('-p', '--publisher',
                            action='store_true',
                            help='')


    def _run(self):
        print(f'{self.name()} running')
