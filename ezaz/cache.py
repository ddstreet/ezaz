
from contextlib import suppress
from datetime import datetime
from datetime import timedelta
from datetime import timezone
from pathlib import Path

from . import DEFAULT_CACHEPATH
from .exception import CacheExpired
from .exception import CacheMiss
from .exception import InvalidCache
from .exception import InvalidCacheExpiry


DEFAULT_CACHENAME = 'cache'
DEFAULT_CACHE = DEFAULT_CACHEPATH / DEFAULT_CACHENAME


class BaseCache:
    def __init__(self, *, cachepath, hashmap, verbose=0, dry_run=False):
        self.cachepath = cachepath
        self.hashmap = hashmap
        self.verbose = verbose
        self.dry_run = dry_run

    def clear(self):
        if dry_run:
            return

        import shutil
        shutil.rmtree(self.cachepath)

    def _is_expired(self, path):
        return False

    def _check_hash(self, path, content):
        return self.hashmap.get(path) == hash(content)

    def _store_hash(self, path, content):
        self.hashmap[path] = hash(content)
        return content

    def _remove_hash(self, path):
        with suppress(KeyError):
            del self.hashmap[path]

    def _read(self, path):
        if not path.is_file():
            raise CacheMiss()
        if self._is_expired(path):
            self._remove(path)
            raise CacheExpired()

        return self._store_hash(path, path.read_text())

    def _write(self, path, content):
        if self.dry_run or self._check_hash(path, content):
            return

        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content)
        self._store_hash(path, content)

    def _remove(self, path):
        if dry_run:
            return

        self._remove_hash(path)
        path.unlink(missing_ok=True)

    def _quote(self, objid):
        from urllib.parse import quote
        return quote(objid)


class ShowCache(BaseCache):
    def showfile(self, *, classname, objid):
        return self.cachepath / f'show_{classname}_{self._quote(objid)}'

    def read_show(self, *, classname, objid):
        return self._read(self.showfile(classname=classname, objid=objid))

    def write_show(self, *, classname, objid, content):
        self._write(self.showfile(classname=classname, objid=objid), content)

    def invalidate_show(self, *, classname, objid):
        self._remove(self.showfile(classname=classname, objid=objid))


class ListCache(BaseCache):
    def listfile(self, *, classname):
        return self.cachepath / f'list_{classname}'

    def read_list(self, *, classname):
        return self._read(self.listfile(classname=classname))

    def write_list(self, *, classname, content):
        self._write(self.listfile(classname=classname), content)

    def invalidate_list(self, *, classname):
        self._remove(self.listfile(classname=classname))


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
        for info in infolist:
            self.write_info(classname=classname, objid=info._id, info=info)

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


class ClassCache(ShowClassCache, ListClassCache, InfoClassCache):
    def object_cache(self, objid):
        return ObjectCache(cachepath=self.cachepath, verbose=self.verbose, dry_run=self.dry_run, hashmap=self.hashmap, classname=self.classname, objid=objid)


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

    def child_class_cache(self, child_classname):
        return ClassCache(cachepath=self._child_cache_dir(), verbose=self.verbose, dry_run=self.dry_run, hashmap=self.hashmap, classname=child_classname)

    def child_object_cache(self, child_classname, child_objid):
        return self.child_class_cache(child_classname).object_cache(child_objid)


class ObjectCache(ParentObjectCache, ShowObjectCache, ListObjectCache, InfoObjectCache):
    pass


class Cache:
    def __init__(self, *, cachepath, verbose, dry_run):
        self.cachepath = Path(cachepath or DEFAULT_CACHE).expanduser().resolve()
        self.verbose = verbose
        self.dry_run = dry_run
        self.hashmap = {}

    def class_cache(self, classname):
        return ClassCache(cachepath=self.cachepath, verbose=self.verbose, dry_run=self.dry_run, hashmap=self.hashmap, classname=classname)

    def object_cache(self, classname, objid):
        return ObjectCache(cachepath=self.cachepath, verbose=self.verbose, dry_run=self.dry_run, hashmap=self.hashmap, classname=classname, objid=objid)


class CacheExpiry:
    NOCACHE = 'nocache'
    FOREVER = 'forever'

    def __init__(self, config={}, *, show_expiry=None, list_expiry=None):
        if isinstance(config, CacheExpiry):
            self._config = config.config
        else:
            self._config = config

        self.show_expiry = show_expiry or self.show_expiry
        self.list_expiry = list_expiry or self.list_expiry

    def is_show_expired(self, entry):
        return is_expired(entry, self.show_expiry)

    def is_list_expired(self, entry):
        return is_expired(entry, self.list_expiry)

    def is_expired(self, entry, expiry):
        if expiry == self.NOCACHE:
            return True
        if expiry == self.FOREVER:
            return False
        try:
            duration = timedelta(seconds=int(float(expiry)))
        except ValueError as ve:
            raise InvalidCacheExpiry(f"Invalid expiration duration '{expiry}': {ve}") from ve
        return self.age(entry) > duration

    def age(self, entry):
        return datetime.now(tz=timezone.utc) - datetime.fromtimestamp(entry.stat().st_mtime, tz=timezone.utc)
