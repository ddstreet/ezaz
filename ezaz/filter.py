
import json
import re

from contextlib import suppress

from .exception import InvalidFilterRegex


KEY_ENABLED = 'enabled'
KEY_REGEX = 'regex'
KEY_PREFIX = 'prefix'
KEY_SUFFIX = 'suffix'


class Filter:
    def __init__(self, *, config):
        self._config = config

    def __repr__(self):
        return json.dumps(dict(self.config), indent=2)

    @property
    def config(self):
        return self._config.get_object('filters')

    @property
    def is_enabled(self):
        return self.config.get(KEY_ENABLED, False)

    def enable(self):
        self.config[KEY_ENABLED] = True

    def disable(self):
        self.config[KEY_ENABLED] = False

    def _get(self, key):
        return self.config.get(key, None)

    def _set(self, key, value):
        if value:
            self.config[key] = value
        else:
            self._clear(key)

    def _clear(self, key):
        with suppress(KeyError):
            del self.config[key]

    def get_prefix(self):
        return self._get(KEY_PREFIX)

    def set_prefix(self, prefix):
        self._set(KEY_PREFIX, prefix)

    def clear_prefix(self):
        self._clear(KEY_PREFIX)

    def get_suffix(self):
        return self._get(KEY_SUFFIX)

    def set_suffix(self, suffix):
        self._set(KEY_SUFFIX, suffix)

    def clear_suffix(self):
        self._clear(KEY_SUFFIX)

    def _check_regex_pattern(self, pattern):
        try:
            if pattern:
                re.compile(pattern)
        except re.PatternError as pe:
            raise InvalidFilterRegex(pattern) from pe

    def get_regex(self):
        return self._get(KEY_REGEX)

    def set_regex(self, pattern):
        self._check_regex_pattern(pattern)
        self._set(KEY_REGEX, pattern)

    def clear_regex(self):
        self._clear(KEY_REGEX)
