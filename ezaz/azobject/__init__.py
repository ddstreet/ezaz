
import json
import subprocess

from abc import ABC
from abc import abstractmethod

from ..response import lookup_response


class AzObject(ABC):
    @classmethod
    @abstractmethod
    def name(cls):
        pass

    def __init__(self, config, verbose=False, dry_run=False):
        self._config = config
        self._verbose = verbose
        self._dry_run = dry_run
        self._setup()

    @property
    def verbose(self):
        return self._verbose

    @property
    def dry_run(self):
        return self._dry_run

    def _setup(self):
        pass

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
