
import re

from .dictnamespace import DictNamespace
from .exception import InvalidFilterRegex


class Filter(DictNamespace):
    def __init__(self, config, *, prefix=None, suffix=None, regex=None):
        super().__init__(config)

        # The direct params override the config
        # Also, ensure all 3 fields exist
        self.prefix = prefix or getattr(self, 'prefix', None)
        self.suffix = suffix or getattr(self, 'suffix', None)
        self.regex = regex or getattr(self, 'regex', None)

    def __bool__(self):
        return any((self.prefix, self.suffix, self.regex))

    def _validate_regex_patterns(self, patterns):
        for pattern in patterns:
            try:
                re.compile(pattern)
            except re.PatternError as pe:
                raise InvalidFilterRegex(pattern) from pe

    def __setattr__(self, attr, value):
        if value and attr in ['prefix', 'suffix', 'regex']:
            if isinstance(value, str):
                value = [value]
            if attr == 'regex':
                self._validate_regex_patterns(value)
        super().__setattr__(attr, value)

    @property
    def requires_info(self):
        for l in (self.prefix, self.suffix, self.regex):
            if any(('=' in f for f in l or [])):
                # If any filter specifies a field, we need the entire info
                return True
        return False

    def check(self, info):
        return all((self.check_prefix(info), self.check_suffix(info), self.check_regex(info)))

    def check_prefix(self, info):
        return self._check_filters(info, None, self.prefix, self._check_prefix)

    def check_suffix(self, info):
        return self._check_filters(info, None, self.suffix, self._check_suffix)

    def check_regex(self, info):
        return self._check_filters(info, None, self.regex, self._check_regex)

    def check_id(self, value):
        return all((self.check_id_prefix(info), self.check_id_suffix(info), self.check_id_regex(info)))

    def check_id_prefix(self, info_id):
        return self._check_filters(None, info_id, self.prefix, self._check_prefix)

    def check_id_suffix(self, info_id):
        return self._check_filters(None, info_id, self.suffix, self._check_suffix)

    def check_id_regex(self, info_id):
        return self._check_filters(None, info_id, self.regex, self._check_regex)

    def _check_filters(self, info, info_id, filters, check_fn):
        for f in filters or []:
            if '=' not in f:
                f = '=' + f
            field, _, check_value = f.partition('=')
            if field:
                if not info:
                    raise FilterRequiresInfo()
                value = info._path_attr_getter(field)(info) or ''
            else:
                value = info._id if info else info_id
            if not check_fn(value, check_value):
                return False
        return True

    def _check_prefix(self, value, prefix):
        return value.startswith(prefix)

    def _check_suffix(self, value, suffix):
        return value.endswith(suffix)

    def _check_regex(self, value, regex):
        return re.search(regex, value)
