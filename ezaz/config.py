
import json

from collections.abc import Mapping
from collections.abc import MutableMapping
from contextlib import suppress
from functools import partial
from pathlib import Path

from . import DEFAULT_CONFIGPATH


DEFAULT_FILENAME = 'config.json'
DEFAULT_CONFIGFILE = DEFAULT_CONFIGPATH / DEFAULT_FILENAME


class SubConfig(MutableMapping):
    def __init__(self, config, mapping):
        self._config = config
        self._mapping = mapping

    def __getitem__(self, key):
        return self._mapping[key]

    def __setitem__(self, key, value):
        if value is None:
            with suppress(KeyError):
                del self[key]
        else:
            if isinstance(value, Mapping):
                value = SubConfig(self._config, value)
            self._mapping[key] = value
            self._config._save()

    def __delitem__(self, key):
        del self._mapping[key]
        self._config._save()

    def __iter__(self):
        return iter(self._mapping)

    def __len__(self):
        return len(self._mapping)

    def setdefault(self, key, value):
        with suppress(KeyError):
            return self[key]
        self[key] = value
        return self[key]

    def get_object(self, key):
        # get the specified object, or insert and return a new empty one
        return self.setdefault(key, {})


class Config(SubConfig):
    def __init__(self, configfile=DEFAULT_CONFIGFILE):
        self._configfile = Path(configfile).expanduser().resolve()
        super().__init__(self, self._read_config())
        self._file_config = self._prep_file_config(self)
        # TODO - check with jsonschema

    def _read_config(self):
        try:
            return json.loads(self._configfile.read_text(), object_hook=partial(SubConfig, self))
        except FileNotFoundError:
            return SubConfig(self, {})

    def _prep_file_config(self, d):
        # Copy everything except empty dicts, which we don't need to save
        cleand = {}
        for k, v in d.items():
            if isinstance(v, Mapping):
                v = self._prep_file_config(v)
                if not v:
                    continue
            cleand[k] = v
        return cleand

    def _save(self):
        file_config = self._prep_file_config(self)
        if file_config == self._file_config:
            return

        self._file_config = file_config
        self._configfile.parent.mkdir(parents=True, exist_ok=True)
        self._configfile.write_text(str(self) + '\n')

    def __repr__(self):
        return json.dumps(self._file_config, indent=2, sort_keys=True)

    def remove(self):
        self._configfile.unlink(missing_ok=True)
        self.__init__(configfile=self._configfile)
