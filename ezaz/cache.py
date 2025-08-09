
from datetime import datetime
from datetime import timedelta
from pathlib import Path

from .exception import CacheExpired
from .exception import CacheMiss
from . import DEFAULT_CACHEPATH


DEFAULT_CACHENAME = 'cache'
DEFAULT_CACHE = DEFAULT_CACHEPATH / DEFAULT_CACHENAME
DEFAULT_MAX_AGE = timedelta(minutes=1)


class Cache:
    def __init__(self, cachepath=None, max_age=None):
        self._cachepath = Path(cachepath or DEFAULT_CACHE).expanduser().resolve()
        self._max_age = max_age or DEFAULT_MAX_AGE

    def read(self, cmd):
        if cmd:
            return self._read_path(self._cmd_path(self._cachepath, cmd))
        return None

    def write(self, cmd, response):
        if cmd and response:
            self._write_path(self._cmd_path(self._cachepath, cmd), response)

    def _cmd_path(self, path, cmd):
        if not cmd or cmd[0].startswith('-'):
            return path / self._cmd_filename(cmd)
        return self._cmd_path(path / cmd[0], cmd[1:])

    def _cmd_filename(self, cmd):
        if not cmd:
            return 'NOARGS'
        return ' '.join(cmd)

    def _read_path(self, path):
        if not path.is_file():
            raise CacheMiss()
        if self._path_expired(path):
            path.unlink()
            raise CacheExpired()
        return path.read_text()

    def _write_path(self, path, response):
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(response)

    def _path_age(self, path):
        return datetime.now() - datetime.fromtimestamp(path.stat().st_mtime)

    def _path_expired(self, path):
        return self._path_age(path) > self.max_age

    @property
    def max_age(self):
        return self._max_age
