
import json
import subprocess

from abc import ABC
from abc import abstractmethod

from ..response import lookup_response


class Command(ABC):
    @classmethod
    @abstractmethod
    def name(cls):
        pass

    @classmethod
    def aliases(cls):
        return []

    @classmethod
    def parser_add_subparser(cls, subparsers):
        parser = subparsers.add_parser(cls.name(),
                                       aliases=cls.aliases())
        cls.parser_add_arguments(parser)
        parser.set_defaults(cls=cls)
        return parser

    @classmethod
    def parser_add_arguments(cls, parser):
        parser.add_argument('-v', '--verbose',
                            action='store_true',
                            help='Be verbose')
        parser.add_argument('-n', '--dry-run',
                            action='store_true',
                            help='Only print what would be done, do not run commands')
        cls._parser_add_arguments(parser)

    @classmethod
    def _parser_add_arguments(cls, parser):
        pass

    def __init__(self, config, options):
        self._config = config
        self._options = options
        self._setup()

    def _setup(self):
        pass

    @property
    def verbose(self):
        return self._options.verbose

    @property
    def dry_run(self):
        return self._options.dry_run

    def _trace(self, msg):
        if self.verbose or self.dry_run:
            prefix = 'DRY-RUN: ' if self.dry_run else ''
            print(f'{prefix}{msg}')

    def _exec(self, *args, **kwargs):
        defaults = {
            'check': True,
            'text': True,
            'capture_output': False,
        }
        self._trace(' '.join(args))
        if self.dry_run:
            return None
        else:
            return subprocess.run(args, **(defaults | kwargs))

    def az(self, *args, **kwargs):
        self._exec('az', *args, **kwargs)

    def az_stdout(self, *args, **kwargs):
        cp = self._exec('az', *args, capture_output=True, **kwargs)
        return cp.stdout if cp else ''

    def az_json(self, *args, **kwargs):
        stdout = self.az_stdout(*args, **kwargs)
        return json.loads(stdout) if stdout else {}

    def az_response(self, *args, **kwargs):
        cls = lookup_response(*args)
        j = self.az_json(*args, **kwargs)
        return cls(j) if j else None

    def az_responselist(self, *args, **kwargs):
        cls = lookup_response(*args)
        j = self.az_json(*args, **kwargs)
        return cls(j) if j else []

    @abstractmethod
    def run(self):
        pass
