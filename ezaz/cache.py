
import os

from contextlib import suppress
from datetime import datetime
from datetime import timedelta
from datetime import timezone
from pathlib import Path

from . import DEFAULT_CACHEPATH
from .dictnamespace import DictNamespace
from .exception import CacheExpired
from .exception import CacheMiss
from .exception import InvalidCache
from .exception import InvalidCacheExpiry
from .exception import NoCache
from .timing import TIMESTAMP


DEFAULT_CACHENAME = 'cache'
DEFAULT_CACHE = DEFAULT_CACHEPATH / DEFAULT_CACHENAME


class BaseCache:
    def __init__(self, *, cachepath, parent, expiry, verbose=None, dry_run=None, no_cache_read=None, no_cache_write=None):
        self.cachepath = cachepath
        self.parent = parent
        self.expiry = expiry
        self.memcache = parent.memcache if parent else {}
        self._verbose = verbose
        self._dry_run = dry_run
        self._no_cache_read = no_cache_read
        self._no_cache_write = no_cache_write

    @property
    def verbose(self):
        return self.parent.verbose if self._verbose is None else self._verbose

    @property
    def dry_run(self):
        return self.parent.dry_run if self._dry_run is None else self._dry_run

    @property
    def no_cache_read(self):
        return self.parent.no_cache_read if self._no_cache_read is None else self._no_cache_read

    @property
    def no_cache_write(self):
        return self.parent.no_cache_write if self._no_cache_write is None else self._no_cache_write

    @property
    def size(self):
        return sum([Path(dirpath).joinpath(filename).stat().st_size
                    for dirpath, dirnames, filenames in os.walk(str(self.cachepath))
                    for filename in filenames])

    def clear(self):
        self.memcache.clear()

        if self.dry_run:
            return

        import shutil
        shutil.rmtree(self.cachepath)

    def _is_expired(self, *, cachetype, path):
        if cachetype == 'show':
            return self.expiry.is_show_expired(path)
        if cachetype in ['list', 'id_list']:
            return self.expiry.is_list_expired(path)
        raise RuntimeError(f"Unknown cachetype '{cachetype}'")

    def _read(self, *, cachetype, path):
        with suppress(KeyError):
            return self.memcache[path]

        if self.no_cache_read:
            raise NoCache()
        if not path.is_file():
            raise CacheMiss()

        try:
            if self._is_expired(cachetype=cachetype, path=path):
                self._remove(cachetype=cachetype, path=path)
                raise CacheExpired()

            return path.read_text()
        finally:
            TIMESTAMP(f'Cache read {cachetype}')

    def _write(self, *, cachetype, path, content):
        self.memcache[path] = content

        if self.dry_run or self.no_cache_write:
            return

        try:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(content)
        finally:
            TIMESTAMP(f'Cache write {cachetype}')

    def _remove(self, *, cachetype, path):
        self.memcache.pop(path, None)

        if self.dry_run:
            return

        path.unlink(missing_ok=True)

    def _remove_all(self, *, cachetype, path):
        parent_dir = path.parent
        try:
            parent_dir.relative_to(self.cachepath)
        except ValueError:
            raise CacheError(f"Cannot remove cache files in '{parent_dir}' which is outside cache path '{self.cachepath}'")

        if not parent_dir.is_dir():
            return

        name = path.name
        for f in parent_dir.iterdir():
            if f.name.startswith(name):
                self._remove(cachetype=cachetype, path=f)

    def __file(self, *args):
        return self.cachepath / '_'.join(args)

    def _file(self, *, cachetype, classname, objid=None, tag=None):
        return self.__file(*filter(None, (cachetype, tag, classname, self._quote(objid))))

    def _quote(self, objid):
        from urllib.parse import quote
        return quote(objid) if objid else None


class ShowCache(BaseCache):
    def showfile(self, *, classname, objid):
        return self._file(cachetype='show', classname=classname, objid=objid)

    def read_show(self, *, classname, objid):
        return self._read(cachetype='show', path=self.showfile(classname=classname, objid=objid))

    def write_show(self, *, classname, objid, content):
        self._write(cachetype='show', path=self.showfile(classname=classname, objid=objid), content=content)

    def invalidate_show(self, *, classname, objid):
        self._remove(cachetype='show', path=self.showfile(classname=classname, objid=objid))

    def invalidate_show_all(self, *, classname):
        self._remove_all(cachetype='show', path=self.showfile(classname=classname, objid=None))


class ListCache(BaseCache):
    def listfile(self, *, tag=None, classname):
        return self._file(cachetype='list', tag=tag, classname=classname)

    def read_list(self, *, tag=None, classname):
        return self._read(cachetype='list', path=self.listfile(tag=tag, classname=classname))

    def write_list(self, *, tag=None, classname, content):
        self._write(cachetype='list', path=self.listfile(tag=tag, classname=classname), content=content)

    def invalidate_list(self, *, tag=None, classname):
        self._remove(cachetype='list', path=self.listfile(tag=tag, classname=classname))


class IdListCache(BaseCache):
    def idlistfile(self, *, tag=None, classname):
        return self._file(cachetype='id_list', tag=tag, classname=classname)

    def read_id_list(self, *, tag=None, classname):
        import json
        try:
            return json.loads(self._read(cachetype='id_list', path=self.idlistfile(tag=tag, classname=classname)))
        except json.decoder.JSONDecodeError as je:
            raise InvalidCache(f'Invalid id list cache: {je}') from je

    def write_id_list(self, *, tag=None, classname, idlist):
        import json
        try:
            self._write(cachetype='id_list', path=self.idlistfile(tag=tag, classname=classname), content=json.dumps(idlist))
        except TypeError as te:
            raise InvalidCache(f'Invalid id list cache: {te}') from te

    def invalidate_id_list(self, *, tag=None, classname):
        self._remove(cachetype='id_list', path=self.idlistfile(tag=tag, classname=classname))


class InfoCache(ShowCache, ListCache):
    def read_info(self, **kwargs):
        from .azobject.info import Info
        return Info.load(self.read_show(**kwargs), verbose=self.verbose)

    def write_info(self, *, info, **kwargs):
        from .azobject.info import Info
        assert isinstance(info, Info)
        self.write_show(content=info.save(), **kwargs)

    def invalidate_info(self, *, objid, **kwargs):
        self.invalidate_show(objid=objid, **kwargs)

    def invalidate_info_all(self, **kwargs):
        self.invalidate_show_all(**kwargs)

    def read_info_list(self, **kwargs):
        from .azobject.info import Info
        return Info.load_list(self.read_list(**kwargs), verbose=self.verbose)

    def write_info_list(self, *, infolist, **kwargs):
        from .azobject.info import Info
        self.write_list(content=Info.save_list(infolist), **kwargs)

    def invalidate_info_list(self, **kwargs):
        self.invalidate_list(**kwargs)


class ParentCache(BaseCache):
    def _child_cache_dir(self, *, classname, objid):
        return self.cachepath / f'cache_{classname}_{self._quote(objid)}'


class BaseClassCache(BaseCache):
    def __init__(self, *, classname, **kwargs):
        self.classname = classname
        super().__init__(**kwargs)


class ShowClassCache(BaseClassCache, ShowCache):
    def showfile(self, *, classname=None, **kwargs):
        return super().showfile(classname=classname or self.classname, **kwargs)

    def read_show(self, *, classname=None, **kwargs):
        return super().read_show(classname=classname or self.classname, **kwargs)

    def write_show(self, *, classname=None, **kwargs):
        super().write_show(classname=classname or self.classname, **kwargs)

    def invalidate_show(self, *, classname=None, **kwargs):
        super().invalidate_show(classname=classname or self.classname, **kwargs)

    def invalidate_show_all(self, *, classname=None, **kwargs):
        super().invalidate_show_all(classname=classname or self.classname, **kwargs)


class ListClassCache(BaseClassCache, ListCache):
    def listfile(self, *, classname=None, **kwargs):
        return super().listfile(classname=classname or self.classname, **kwargs)

    def read_list(self, *, classname=None, **kwargs):
        return super().read_list(classname=classname or self.classname, **kwargs)

    def write_list(self, *, classname=None, **kwargs):
        super().write_list(classname=classname or self.classname, **kwargs)

    def invalidate_list(self, *, classname=None, **kwargs):
        super().invalidate_list(classname=classname or self.classname, **kwargs)


class IdListClassCache(BaseClassCache, IdListCache):
    def idlistfile(self, *, classname=None, **kwargs):
        return super().idlistfile(classname=classname or self.classname, **kwargs)

    def read_id_list(self, *, classname=None, **kwargs):
        return super().read_id_list(classname=classname or self.classname, **kwargs)

    def write_id_list(self, *, classname=None, **kwargs):
        super().write_id_list(classname=classname or self.classname, **kwargs)

    def invalidate_id_list(self, *, classname=None, **kwargs):
        super().invalidate_id_list(classname=classname or self.classname, **kwargs)


class InfoClassCache(BaseClassCache, InfoCache):
    def read_info(self, *, classname=None, **kwargs):
        return super().read_info(classname=classname or self.classname, **kwargs)

    def write_info(self, *, classname=None, **kwargs):
        super().write_info(classname=classname or self.classname, **kwargs)

    def invalidate_info(self, *, classname=None, **kwargs):
        super().invalidate_info(classname=classname or self.classname, **kwargs)

    def invalidate_info_all(self, *, classname=None, **kwargs):
        super().invalidate_info_all(classname=classname or self.classname, **kwargs)

    def read_info_list(self, *, classname=None, **kwargs):
        return super().read_info_list(classname=classname or self.classname, **kwargs)

    def write_info_list(self, *, classname=None, **kwargs):
        super().write_info_list(classname=classname or self.classname, **kwargs)

    def invalidate_info_list(self, *, classname=None, **kwargs):
        super().invalidate_info_list(classname=classname or self.classname, **kwargs)


class ParentClassCache(BaseClassCache, ParentCache):
    def _child_cache_dir(self, *, classname=None, **kwargs):
        return super()._child_cache_dir(classname=classname or self.classname, **kwargs)


class ClassCache(ShowClassCache, ListClassCache, IdListClassCache, InfoClassCache):
    def object_cache(self, expiry, objid):
        return ObjectCache(cachepath=self.cachepath, parent=self, expiry=expiry, classname=self.classname, objid=objid)


class BaseObjectCache(BaseClassCache):
    def __init__(self, *, objid, **kwargs):
        self.objid = objid
        super().__init__(**kwargs)


class ShowObjectCache(BaseObjectCache, ShowClassCache):
    def showfile(self, *, objid=None, **kwargs):
        return super().showfile(objid=objid or self.objid, **kwargs)

    def read_show(self, *, objid=None, **kwargs):
        return super().read_show(objid=objid or self.objid, **kwargs)

    def write_show(self, *, objid=None, **kwargs):
        super().write_show(objid=objid or self.objid, **kwargs)

    def invalidate_show(self, *, objid=None, **kwargs):
        super().invalidate_show(objid=objid or self.objid, **kwargs)


class ListObjectCache(BaseObjectCache, ListClassCache):
    pass


class IdListObjectCache(BaseObjectCache, IdListClassCache):
    pass


class InfoObjectCache(BaseObjectCache, InfoClassCache):
    def read_info(self, *, objid=None, **kwargs):
        return super().read_info(objid=objid or self.objid, **kwargs)

    def write_info(self, *, objid=None, **kwargs):
        super().write_info(objid=objid or self.objid, **kwargs)

    def invalidate_info(self, *, objid=None, **kwargs):
        super().invalidate_info(objid=objid or self.objid, **kwargs)


class ParentObjectCache(BaseObjectCache, ParentClassCache):
    def _child_cache_dir(self, *, classname=None, objid=None):
        # Note - this dir is named for the parent, not the child,
        # meaning all children share their parent's cache
        return super()._child_cache_dir(classname=classname, objid=objid or self.objid)

    def child_class_cache(self, expiry, child_classname):
        return ClassCache(cachepath=self._child_cache_dir(), parent=self, expiry=expiry, classname=child_classname)

    def child_object_cache(self, expiry, child_classname, child_objid):
        return ObjectCache(cachepath=self._child_cache_dir(), parent=self, expiry=expiry, classname=child_classname, objid=child_objid)


class ObjectCache(ParentObjectCache, ShowObjectCache, ListObjectCache, IdListObjectCache, InfoObjectCache):
    pass


class Cache:
    def __init__(self, *, cachepath, verbose, dry_run, no_cache_read, no_cache_write):
        self.cachepath = Path(cachepath or DEFAULT_CACHE).expanduser().resolve()
        self.verbose = verbose
        self.dry_run = dry_run
        self.no_cache_read = no_cache_read
        self.no_cache_write = no_cache_write

    def class_cache(self, expiry, classname):
        return ClassCache(cachepath=self.cachepath,
                          parent=None,
                          expiry=expiry,
                          classname=classname,
                          verbose=self.verbose,
                          dry_run=self.dry_run,
                          no_cache_read=self.no_cache_read,
                          no_cache_write=self.no_cache_write)

    def object_cache(self, expiry, classname, objid):
        return ObjectCache(cachepath=self.cachepath,
                           parent=None,
                           expiry=expiry,
                           classname=classname,
                           objid=objid,
                           verbose=self.verbose,
                           dry_run=self.dry_run,
                           no_cache_read=self.no_cache_read,
                           no_cache_write=self.no_cache_write)


class CacheExpiry(DictNamespace):
    NOCACHE = 'nocache'
    FOREVER = 'forever'
    DEFAULT = NOCACHE

    def __init__(self, config, *, show_expiry=None, list_expiry=None):
        super().__init__(config)

        self.show_expiry = show_expiry or getattr(self, 'show_expiry', None)
        self.list_expiry = list_expiry or getattr(self, 'list_expiry', None)

    def __bool__(self):
        return bool(self.show_expiry or self.list_expiry)

    def is_show_expired(self, entry):
        return self.is_expired(entry, self.show_expiry)

    def is_list_expired(self, entry):
        return self.is_expired(entry, self.list_expiry)

    def is_expired(self, entry, expiry):
        if expiry is None:
            expiry = self.DEFAULT
        if expiry == self.FOREVER:
            return False
        if expiry == self.NOCACHE:
            return True
        try:
            duration = timedelta(seconds=int(float(expiry)))
        except ValueError as ve:
            raise InvalidCacheExpiry(f"Invalid expiration duration '{expiry}': {ve}") from ve
        return self.age(entry) > duration

    def age(self, entry):
        return datetime.now(tz=timezone.utc) - datetime.fromtimestamp(entry.stat().st_mtime, tz=timezone.utc)
