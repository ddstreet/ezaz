
from datetime import datetime
from datetime import timedelta
from pathlib import Path

from . import DEFAULT_CACHEPATH
from .exception import CacheExpired
from .exception import CacheMiss
from .exception import InvalidCache


DEFAULT_CACHENAME = 'cache'
DEFAULT_CACHE = DEFAULT_CACHEPATH / DEFAULT_CACHENAME


class BaseCache:
    def __init__(self, *, cachepath, hashmap, verbose=0, dry_run=False):
        self.cachepath = cachepath
        self.hashmap = hashmap
        self.verbose = verbose
        self.dry_run = dry_run

    def clear(self):
        import shutil
        shutil.rmtree(self.cachepath)

    def _read_path(self, path):
        if not path.is_file():
            raise CacheMiss()
        if self._path_expired(path):
            path.unlink()
            raise CacheExpired()
        content = path.read_text()
        self.hashmap[path] = hash(content)
        return content

    def _write_path(self, path, content):
        if self.dry_run:
            return
        if self.hashmap.get(path) == hash(content):
            return
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content)

    def _path_expired(self, path):
        return False

    def _read(self, path):
        return self._read_path(path)

    def _write(self, path, content):
        self._write_path(path, content)

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


class ListCache(BaseCache):
    def listfile(self, *, classname):
        return self.cachepath / f'list_{classname}'

    def read_list(self, *, classname):
        return self._read(self.listfile(classname=classname))

    def write_list(self, *, classname, content):
        self._write(self.listfile(classname=classname), content)


class InfoCache(ShowCache, ListCache):
    def read_info(self, *, classname, objid):
        from .azobject.info import Info
        return Info.load(self.read_show(classname=classname, objid=objid), verbose=self.verbose)

    def write_info(self, *, classname, objid, info):
        from .azobject.info import Info
        assert isinstance(info, Info)
        self.write_show(classname=classname, objid=objid, content=info.save())

    def read_info_list(self, *, classname):
        from .azobject.info import Info
        return Info.load_list(self.read_list(classname=classname), verbose=self.verbose)

    def write_info_list(self, *, classname, infolist):
        from .azobject.info import Info
        self.write_list(classname=classname, content=Info.save_list(infolist))
        for info in infolist:
            self.write_info(classname=classname, objid=info._id, info=info)


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


class ListClassCache(BaseClassCache, ListCache):
    def listfile(self, *, classname=None):
        return super().listfile(classname=classname or self.classname)

    def read_list(self, *, classname=None):
        return super().read_list(classname=classname or self.classname)

    def write_list(self, *, classname=None, content):
        super().write_list(classname=classname or self.classname, content=content)


class InfoClassCache(BaseClassCache, InfoCache):
    def read_info(self, *, classname=None, objid):
        return super().read_info(classname=classname or self.classname, objid=objid)

    def write_info(self, *, classname=None, objid, info):
        super().write_info(classname=classname or self.classname, objid=objid, info=info)

    def read_info_list(self, *, classname=None):
        return super().read_info_list(classname=classname or self.classname)

    def write_info_list(self, *, classname=None, infolist):
        super().write_info_list(classname=classname or self.classname, infolist=infolist)


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


class ListObjectCache(BaseObjectCache, ListClassCache):
    pass


class InfoObjectCache(BaseObjectCache, InfoClassCache):
    def read_info(self, *, classname=None, objid=None):
        return super().read_info(classname=classname, objid=objid or self.objid)

    def write_info(self, *, classname=None, objid=None, info):
        super().write_info(classname=classname, objid=objid or self.objid, info=info)


class ParentObjectCache(BaseObjectCache, ParentClassCache):
    def _child_cache_dir(self, *, classname=None, objid=None):
        return super()._child_cache_dir(classname=classname, objid=objid or self.objid)

    def child_class_cache(self, classname):
        return ClassCache(cachepath=self._child_cache_dir(), verbose=self.verbose, dry_run=self.dry_run, hashmap=self.hashmap, classname=classname)

    def child_object_cache(self, classname, objid):
        return self.child_class_cache(classname).object_cache(objid)


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
