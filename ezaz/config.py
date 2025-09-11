
import json

from collections.abc import Mapping
from collections.abc import MutableMapping
from contextlib import suppress
from copy import copy
from functools import partial
from pathlib import Path

from . import DEFAULT_CONFIGPATH


DEFAULT_FILENAME = 'config.json'
DEFAULT_CONFIGFILE = DEFAULT_CONFIGPATH / DEFAULT_FILENAME


class SubConfig(MutableMapping):
    def __init__(self, parent, mapping):
        self._parent = parent
        self._mapping = mapping

    def __repr__(self):
        return json.dumps(copy(self), indent=2, sort_keys=True)

    def __copy__(self):
        # Copy everything except empty dicts and None values
        return {k: c for k, v in self.items() for c in [copy(v)] if c is not None} or None

    def __equals__(self, other):
        if isinstance(other, Mapping):
            return other == self._mapping
        return super().__equals__(other)

    def __getitem__(self, key):
        return self._mapping[key]

    def __setitem__(self, key, value):
        if isinstance(value, Mapping):
            value = SubConfig(self, value)
        self._mapping[key] = value
        self.save()

    def __delitem__(self, key):
        del self._mapping[key]
        self.save()

    def __iter__(self):
        return iter(self._mapping)

    def __len__(self):
        return len(self._mapping)

    @property
    def parent(self):
        return self._parent

    @property
    def configfile(self):
        return self.parent.configfile

    def save(self):
        return self.parent.save()

    def setdefault(self, key, value):
        with suppress(KeyError):
            v = self[key]
            # We consider None value == missing key
            if v is not None:
                return v
        self[key] = value
        return self[key]

    def get_object(self, key):
        # get the specified object, or insert and return a new empty one
        return self.setdefault(key, {})


class Config(SubConfig):
    def __init__(self, configfile=None):
        self._configfile = Path(configfile or DEFAULT_CONFIGFILE).expanduser().resolve()
        super().__init__(self, self._read_config())
        self._file_config = copy(self)
        # TODO - check with jsonschema

    def __copy__(self):
        return super().__copy__() or {}

    def _read_config(self):
        try:
            return json.loads(self.configfile.read_text(), object_hook=partial(SubConfig, self))
        except FileNotFoundError:
            return SubConfig(self, {})

    @property
    def parent(self):
        return self

    @property
    def configfile(self):
        return self._configfile

    def save(self):
        file_config = copy(self)
        if file_config == self._file_config:
            return

        self._file_config = file_config
        self.configfile.parent.mkdir(parents=True, exist_ok=True)
        self.configfile.write_text(str(self) + '\n')

    def remove(self):
        self.configfile.unlink(missing_ok=True)
        self.__init__(configfile=self.configfile)
