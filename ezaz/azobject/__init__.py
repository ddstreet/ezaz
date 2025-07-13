
import json
import subprocess

from abc import ABC
from abc import abstractmethod

from ..exception import NotLoggedIn
from ..response import lookup_response


class AzObject:
    @property
    @abstractmethod
    def config(self):
        pass

    @property
    def verbose(self):
        return self.config.verbose

    @property
    def dry_run(self):
        return self.config.dry_run

    def _trace(self, msg):
        if self.verbose or self.dry_run:
            prefix = 'DRY-RUN: ' if self.dry_run else ''
            print(f'{prefix}{msg}')

    def _exec(self, *args, check=True, text=True, **kwargs):
        self._trace(' '.join(args))
        return None if self.dry_run else subprocess.run(args, check=check, text=text, **kwargs)

    def az(self, *args, capture_output=False, **kwargs):
        return self._exec('az', *args, capture_output=capture_output, **kwargs)

    def az_stdout(self, *args, **kwargs):
        try:
            cp = self.az(*args, capture_output=True, **kwargs)
        except subprocess.CalledProcessError as cpe:
            if "Please run 'az login' to setup account" in cpe.stderr:
                raise NotLoggedIn()
            else:
                raise
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
