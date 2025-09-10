
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
    def __init__(self, *, cachepath, expiry, cachecfg, hashmap={}):
        self.cachepath = cachepath
        self.expiry = expiry
        self.cachecfg = cachecfg
        self.hashmap = hashmap

    @property
    def verbose(self):
        return self.cachecfg.verbose

    @property
    def dry_run(self):
        return self.cachecfg.dry_run

    @property
    def no_cache_read(self):
        return self.cachecfg.no_cache_read

    @property
    def no_cache_write(self):
        return self.cachecfg.no_cache_write

    def clear(self):
        if self.dry_run:
            return

        import shutil
        shutil.rmtree(self.cachepath)

    def _check_hash(self, path, content):
        return self.hashmap.get(path) == hash(content)

    def _store_hash(self, path, content):
        self.hashmap[path] = hash(content)
        return content

    def _remove_hash(self, path):
        with suppress(KeyError):
            del self.hashmap[path]

    def _is_expired(self, *, cachetype, path):
        if cachetype == 'show':
            return self.expiry.is_show_expired(path)
        if cachetype in ['list', 'id_list']:
            return self.expiry.is_list_expired(path)
        raise RuntimeError(f"Unknown cachetype '{cachetype}'")

    def _read(self, *, cachetype, path):
        if self.no_cache_read:
            raise NoCache()
        if not path.is_file():
            raise CacheMiss()

        try:
            if self._is_expired(cachetype=cachetype, path=path):
                self._remove(cachetype=cachetype, path=path)
                raise CacheExpired()

            return self._store_hash(path, path.read_text())
        finally:
            TIMESTAMP(f'Cache read {cachetype}')

    def _write(self, *, cachetype, path, content):
        if self.dry_run or self.no_cache_write or self._check_hash(path, content):
            return

        try:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(content)
            self._store_hash(path, content)
        finally:
            TIMESTAMP(f'Cache write {cachetype}')

    def _remove(self, *, cachetype, path):
        if self.dry_run:
            return

        self._remove_hash(path)
        path.unlink(missing_ok=True)

    def __file(self, *args):
        return self.cachepath / '_'.join(args)

    def _file(self, *, cachetype, classname, objid=None):
        if objid:
            return self.__file(cachetype, classname, self._quote(objid))
        else:
            return self.__file(cachetype, classname)

    def _quote(self, objid):
        from urllib.parse import quote
        return quote(objid)


class ShowCache(BaseCache):
    def showfile(self, *, classname, objid):
        return self._file(cachetype='show', classname=classname, objid=objid)

    def read_show(self, *, classname, objid):
        return self._read(cachetype='show', path=self.showfile(classname=classname, objid=objid))

    def write_show(self, *, classname, objid, content):
        self._write(cachetype='show', path=self.showfile(classname=classname, objid=objid), content=content)

    def invalidate_show(self, *, classname, objid):
        self._remove(cachetype='show', path=self.showfile(classname=classname, objid=objid))


class ListCache(BaseCache):
    def listfile(self, *, classname):
        return self._file(cachetype='list', classname=classname)

    def read_list(self, *, classname):
        return self._read(cachetype='list', path=self.listfile(classname=classname))

    def write_list(self, *, classname, content):
        self._write(cachetype='list', path=self.listfile(classname=classname), content=content)

    def invalidate_list(self, *, classname):
        self._remove(cachetype='list', path=self.listfile(classname=classname))


class IdListCache(BaseCache):
    def idlistfile(self, *, classname):
        return self._file(cachetype='id_list', classname=classname)

    def read_id_list(self, *, classname):
        import json
        try:
            return json.loads(self._read(cachetype='id_list', path=self.idlistfile(classname=classname)))
        except json.decoder.JSONDecodeError as je:
            raise InvalidCache(f'Invalid id list cache: {je}') from je

    def write_id_list(self, *, classname, idlist):
        import json
        try:
            self._write(cachetype='id_list', path=self.idlistfile(classname=classname), content=json.dumps(idlist))
        except TypeError as te:
            raise InvalidCache(f'Invalid id list cache: {te}') from te

    def invalidate_id_list(self, *, classname):
        self._remove(cachetype='id_list', path=self.idlistfile(classname=classname))


class InfoCache(ShowCache, ListCache):
    def read_info(self, *, classname, objid):
        from .azobject.info import Info
        return Info.load(self.read_show(classname=classname, objid=objid), verbose=self.verbose)

    def write_info(self, *, classname, objid, info):
        from .azobject.info import Info
        assert isinstance(info, Info)
        self.write_show(classname=classname, objid=objid, content=info.save())

    def invalidate_info(self, *, classname, objid):
        self.invalidate_show(classname=classname, objid=objid)
        self.invalidate_info_list(classname=classname)

    def read_info_list(self, *, classname):
        from .azobject.info import Info
        return Info.load_list(self.read_list(classname=classname), verbose=self.verbose)

    def write_info_list(self, *, classname, infolist):
        from .azobject.info import Info
        self.write_list(classname=classname, content=Info.save_list(infolist))

    def invalidate_info_list(self, *, classname):
        self.invalidate_list(classname=classname)


class ParentCache(BaseCache):
    def _child_cache_dir(self, *, classname, objid):
        return self.cachepath / f'cache_{classname}_{self._quote(objid)}'


class BaseClassCache(BaseCache):
    def __init__(self, *, classname, **kwargs):
        self.classname = classname
        super().__init__(**kwargs)


class ShowClassCache(BaseClassCache, ShowCache):
    def showfile(self, *, classname=None, objid):
        return super().showfile(classname=classname or self.classname, objid=objid)

    def read_show(self, *, classname=None, objid):
        return super().read_show(classname=classname or self.classname, objid=objid)

    def write_show(self, *, classname=None, objid, content):
        super().write_show(classname=classname or self.classname, objid=objid, content=content)

    def invalidate_show(self, *, classname=None, objid):
        super().invalidate_show(classname=classname or self.classname, objid=objid)


class ListClassCache(BaseClassCache, ListCache):
    def listfile(self, *, classname=None):
        return super().listfile(classname=classname or self.classname)

    def read_list(self, *, classname=None):
        return super().read_list(classname=classname or self.classname)

    def write_list(self, *, classname=None, content):
        super().write_list(classname=classname or self.classname, content=content)

    def invalidate_list(self, *, classname=None):
        super().invalidate_list(classname=classname or self.classname)


class IdListClassCache(BaseClassCache, IdListCache):
    def idlistfile(self, *, classname=None):
        return super().idlistfile(classname=classname or self.classname)

    def read_id_list(self, *, classname=None):
        return super().read_id_list(classname=classname or self.classname)

    def write_id_list(self, *, classname=None, idlist):
        super().write_id_list(classname=classname or self.classname, idlist=idlist)

    def invalidate_id_list(self, *, classname=None):
        super().invalidate_id_list(classname=classname or self.classname)


class InfoClassCache(BaseClassCache, InfoCache):
    def read_info(self, *, classname=None, objid):
        return super().read_info(classname=classname or self.classname, objid=objid)

    def write_info(self, *, classname=None, objid, info):
        super().write_info(classname=classname or self.classname, objid=objid, info=info)

    def invalidate_info(self, *, classname=None, objid):
        super().invalidate_info(classname=classname or self.classname, objid=objid)

    def read_info_list(self, *, classname=None):
        return super().read_info_list(classname=classname or self.classname)

    def write_info_list(self, *, classname=None, infolist):
        super().write_info_list(classname=classname or self.classname, infolist=infolist)

    def invalidate_info_list(self, *, classname=None):
        super().invalidate_info_list(classname=classname or self.classname)


class ParentClassCache(BaseClassCache, ParentCache):
    def _child_cache_dir(self, *, classname=None, objid):
        return super()._child_cache_dir(classname=classname or self.classname, objid=objid)


class ClassCache(ShowClassCache, ListClassCache, IdListClassCache, InfoClassCache):
    def object_cache(self, expiry, objid):
        return ObjectCache(cachepath=self.cachepath, expiry=expiry, cachecfg=self.cachecfg, hashmap=self.hashmap, classname=self.classname, objid=objid)


class BaseObjectCache(BaseClassCache):
    def __init__(self, *, objid, **kwargs):
        self.objid = objid
        super().__init__(**kwargs)


class ShowObjectCache(BaseObjectCache, ShowClassCache):
    def showfile(self, *, classname=None, objid=None):
        return super().showfile(classname=classname, objid=objid or self.objid)

    def read_show(self, *, classname=None, objid=None):
        return super().read_show(classname=classname, objid=objid or self.objid)

    def write_show(self, *, classname=None, objid=None, content):
        super().write_show(classname=classname, objid=objid or self.objid, content=content)

    def invalidate_show(self, *, classname=None, objid=None):
        super().invalidate_show(classname=classname, objid=objid or self.objid)


class ListObjectCache(BaseObjectCache, ListClassCache):
    pass


class IdListObjectCache(BaseObjectCache, IdListClassCache):
    pass


class InfoObjectCache(BaseObjectCache, InfoClassCache):
    def read_info(self, *, classname=None, objid=None):
        return super().read_info(classname=classname, objid=objid or self.objid)

    def write_info(self, *, classname=None, objid=None, info):
        super().write_info(classname=classname, objid=objid or self.objid, info=info)

    def invalidate_info(self, *, classname=None, objid=None):
        super().invalidate_info(classname=classname, objid=objid or self.objid)


class ParentObjectCache(BaseObjectCache, ParentClassCache):
    def _child_cache_dir(self, *, classname=None, objid=None):
        # Note - this dir is named for the parent, not the child,
        # meaning all children share their parent's cache
        return super()._child_cache_dir(classname=classname, objid=objid or self.objid)

    def child_class_cache(self, expiry, child_classname):
        return ClassCache(cachepath=self._child_cache_dir(), expiry=expiry, cachecfg=self.cachecfg, classname=child_classname)

    def child_object_cache(self, expiry, child_classname, child_objid):
        return ObjectCache(cachepath=self._child_cache_dir(), expiry=expiry, cachecfg=self.cachecfg, classname=child_classname, objid=child_objid)


class ObjectCache(ParentObjectCache, ShowObjectCache, ListObjectCache, IdListObjectCache, InfoObjectCache):
    pass


class Cache:
    def __init__(self, *, cachepath, verbose, dry_run, no_cache_read, no_cache_write):
        self.cachepath = Path(cachepath or DEFAULT_CACHE).expanduser().resolve()
        self.cachecfg = CacheConfig(verbose=verbose, dry_run=dry_run, no_cache_read=no_cache_read, no_cache_write=no_cache_write)

    def class_cache(self, expiry, classname):
        return ClassCache(cachepath=self.cachepath, expiry=expiry, cachecfg=self.cachecfg, classname=classname)

    def object_cache(self, expiry, classname, objid):
        return ObjectCache(cachepath=self.cachepath, expiry=expiry, cachecfg=self.cachecfg, classname=classname, objid=objid)


class CacheConfig:
    def __init__(self, verbose, dry_run, no_cache_read, no_cache_write):
        self.verbose = verbose
        self.dry_run = dry_run
        self.no_cache_read = no_cache_read
        self.no_cache_write = no_cache_write


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
