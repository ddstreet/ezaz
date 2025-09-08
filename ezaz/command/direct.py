
from functools import cached_property

from ..argutil import PositionalArgConfig
from ..exception import EzazException
from .command import SimpleCommand


class DirectCommand(SimpleCommand):
    @classmethod
    def command_name_list(cls):
        return ['az']

    @classmethod
    def preparse_args(cls, args):
        args.insert(args.index('az') + 1, '--')
        return args

    @classmethod
    def get_simple_command_defaults(cls):
        return dict(preparser=cls.preparse_args)

    @classmethod
    def get_simple_command_parser_kwargs(cls):
        return dict(add_help=False)

    @classmethod
    def get_simple_command_argconfigs(cls):
        return [*super().get_simple_command_argconfigs(),
                PositionalArgConfig('command', remainder=True, help='Command to run (i.e. az COMMAND ...)')]

    @cached_property
    def direct(self):
        from ..azobject.direct import DirectAction
        return DirectAction(verbose=self.verbose, dry_run=self.dry_run)

    def az(self, command, **opts):
        if command and command[0] == '--':
            command = command[1:]
        if not command:
            raise EzazException('Must provide az command')
        if command[0] in ['-h', '--help'] and len(command) == 1:
            opts.get('print_help')()
        else:
            self.direct.az(*command)
