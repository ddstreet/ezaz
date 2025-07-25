
import json
import re

from contextlib import suppress
from functools import partialmethod

from .exception import InvalidFilterRegex


class Filter:
    def __init__(self, config={}, *, prefix=None, suffix=None, regex=None):
        if isinstance(config, Filter):
            self._config = config.config
        else:
            self._config = config

        # This performs validation (of regex) and cleanup of
        # empty/null values
        self.prefix = prefix or self.prefix
        self.suffix = suffix or self.suffix
        self.regex = regex or self.regex

    def __str__(self):
        return json.dumps(dict(self.config))

    def __repr__(self):
        return f'{self.__class__.__name__}(config={repr(self.config)})'

    @property
    def config(self):
        return self._config

    def __bool__(self):
        return bool(self.config)

    def _get(self, key):
        return self.config.get(key, None)

    def _set(self, key, value):
        if value:
            self.config[key] = value
        else:
            self._del(key)

    def _del(self, key):
        with suppress(KeyError):
            del self.config[key]

    def _validate_regex_pattern(self, pattern):
        try:
            if pattern:
                re.compile(pattern)
        except re.PatternError as pe:
            raise InvalidFilterRegex(pattern) from pe

    def _validate_and_set_regex_pattern(self, pattern):
        self._validate_regex_pattern(pattern)
        self._set('regex', pattern)

    _get_prefix = lambda self: self._get('prefix')
    _set_prefix = lambda self, v: self._set('prefix', v)
    _del_prefix = lambda self: self._del('prefix')
    prefix = property(_get_prefix, _set_prefix, _del_prefix)

    _get_suffix = lambda self: self._get('suffix')
    _set_suffix = lambda self, v: self._set('suffix', v)
    _del_suffix = lambda self: self._del('suffix')
    suffix = property(_get_suffix, _set_suffix, _del_suffix)

    _get_regex = lambda self: self._get('regex')
    _set_regex = lambda self, v: self._validate_and_set_regex_pattern(v)
    _del_regex = lambda self: self._del('regex')
    regex = property(_get_regex, _set_regex, _del_regex)

    def check_info(self, info):
        return self.check(info._id)

    def check(self, v):
        return self.check_prefix(v) and self.check_suffix(v) and self.check_regex(v)

    def check_prefix(self, v):
        return v.startswith(self.prefix) if self.prefix else True

    def check_suffix(self, v):
        return v.endswith(self.suffix) if self.suffix else True

    def check_regex(self, v):
        return re.search(self.regex, v) if self.regex else True
