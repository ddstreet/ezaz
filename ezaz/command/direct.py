
from ..azobject.direct import DirectAction
from .command import SimpleCommand


class DirectCommand(SimpleCommand):
    @classmethod
    def command_name_list(cls):
        return ['az']

    @classmethod
    def parser_add_arguments(cls, parser):
        cls.parser_add_common_arguments(parser)
        parser.add_argument('args', nargs='+', help='Run arbitrary az cli commands')

    def _setup(self):
        super()._setup()
        self._direct = DirectAction(verbose=self.verbose, dry_run=self.dry_run)

    def run(self):
        self._direct.az(*self._options.args)
