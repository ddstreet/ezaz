
from .command import Command


class ConfigCommand(Command):
    @classmethod
    def command_name_list(cls):
        return ['config']

    @classmethod
    def _parser_add_arguments(cls, parser):
        parser.add_argument('--show',
                            action='store_true',
                            help='Show config (default)')

    def _run(self):
        print(self._config)
