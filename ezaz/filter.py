
import re

from .dictnamespace import DictNamespace
from .exception import InvalidFilterRegex


class Filter(DictNamespace):
    def __init__(self, config, *, prefix=None, suffix=None, regex=None):
        super().__init__(config)

        self.prefix = prefix or getattr(self, 'prefix', None)
        self.suffix = suffix or getattr(self, 'suffix', None)
        self.regex = regex or getattr(self, 'regex', None)

    def __bool__(self):
        return bool(self.prefix or self.suffix or self.regex)

    def _validate_regex_pattern(self, pattern):
        try:
            if pattern:
                re.compile(pattern)
        except re.PatternError as pe:
            raise InvalidFilterRegex(pattern) from pe

    def __setattr__(self, attr, value):
        if attr == 'regex':
            self._validate_regex_pattern(value)
        super().__setattr__(attr, value)

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
