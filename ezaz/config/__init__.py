
import json

from contextlib import suppress
from copy import deepcopy
from pathlib import Path

from .. import DEFAULT_CONFIGPATH
from ..exception import AccountConfigNotFound
from .account import AccountConfig


DEFAULT_FILENAME = 'config.json'
DEFAULT_CONFIGFILE = DEFAULT_CONFIGPATH / DEFAULT_FILENAME


class Config:
    @classmethod
    def _ACCOUNT_KEY(cls, account):
        return f'account:{account}'

    def __init__(self, configfile=DEFAULT_CONFIGFILE, verbose=False, dry_run=False):
        self._configfile = Path(configfile).expanduser()
        self._config = json.loads(self._configfile.read_text()) if self._configfile.is_file() else {}

        # verbose and dry_run are only valid for the current session, not saved to config file
        self._verbose = verbose
        self._dry_run = dry_run

        # TODO - check jsonschema instead
        if not isinstance(self._config, dict):
            raise RuntimeError(f"Invalid config: '{self._configfile}'")

    @property
    def verbose(self):
        return self._verbose

    @property
    def dry_run(self):
        return self._dry_run

    def _remove_empty_dicts(self, d):
        # Copy everything except empty dicts, which we don't need to save
        cleand = {}
        for k, v in d.items():
            if isinstance(v, dict):
                v = self._remove_empty_dicts(v)
                if not v:
                    continue
            cleand[k] = v
        return cleand

    def _save(self):
        self._configfile.parent.mkdir(parents=True, exist_ok=True)
        self._configfile.write_text(str(self) + '\n')

    def __repr__(self):
        return json.dumps(self._remove_empty_dicts(self._config), indent=2, sort_keys=True)

    def get_account(self, account):
        k = self._ACCOUNT_KEY(account)
        return AccountConfig(self, self._config.setdefault(k, {}))

    def del_account(self, account):
        k = self._ACCOUNT_KEY(account)
        with suppress(KeyError):
            del self._config[k]
            self._save()
