
import json
import subprocess

from abc import ABC
from abc import abstractmethod
from contextlib import suppress
from functools import partialmethod

from ..exception import NotLoggedIn
from ..response import lookup_response


class AzObject(ABC):
    @property
    @abstractmethod
    def config(self):
        pass

    @property
    def verbose(self):
        return self.config.verbose

    @property
    def dry_run(self):
        return self.config.dry_run

    def _trace(self, msg):
        if self.verbose or self.dry_run:
            prefix = 'DRY-RUN: ' if self.dry_run else ''
            print(f'{prefix}{msg}')

    def _exec(self, *args, check=True, text=True, **kwargs):
        self._trace(' '.join(args))
        return None if self.dry_run else subprocess.run(args, check=check, text=text, **kwargs)

    def az(self, *args, capture_output=False, **kwargs):
        return self._exec('az', *args, capture_output=capture_output, **kwargs)

    def az_stdout(self, *args, **kwargs):
        try:
            cp = self.az(*args, capture_output=True, **kwargs)
        except subprocess.CalledProcessError as cpe:
            if "Please run 'az login' to setup account" in cpe.stderr:
                raise NotLoggedIn()
            else:
                raise
        return cp.stdout if cp else ''

    def az_json(self, *args, **kwargs):
        stdout = self.az_stdout(*args, **kwargs)
        return json.loads(stdout) if stdout else {}

    def az_response(self, *args, **kwargs):
        cls = lookup_response(*args)
        j = self.az_json(*args, **kwargs)
        return cls(j) if j else None

    def az_responselist(self, *args, **kwargs):
        cls = lookup_response(*args)
        j = self.az_json(*args, **kwargs)
        return cls(j) if j else []


class StandardAzObjectSubclass(AzObject):
    @classmethod
    @abstractmethod
    def _cls_type(cls):
        pass

    @classmethod
    def _cls_info_id(cls, info):
        # Most use 'name'
        return info.name

    @classmethod
    @abstractmethod
    def _cls_config_not_found(cls):
        pass

    @classmethod
    @abstractmethod
    def _cls_show_info_cmd(cls):
        pass

    @classmethod
    @abstractmethod
    def _cls_list_info_cmd(cls):
        pass


def StandardAzObjectTemplate(subclasses=[]):
    class StandardAzObject(StandardAzObjectSubclass):
        def __init__(self, obj_id, parent, info=None):
            self._obj_id = obj_id
            self._parent = parent
            self._info = info

        @property
        def config(self):
            return getattr(self.parent.config, f'get_{self._cls_type()}')(self.object_id)

        @property
        def object_id(self):
            return self._obj_id

        @property
        def name(self):
            return self.info.name

        @property
        def parent(self):
            return self._parent

        @abstractmethod
        def _info_opts(self):
            pass

        def _get_info(self):
            return self.az_response(*self._cls_show_info_cmd(), *self._info_opts())

        @property
        def info(self):
            if not self._info:
                self._info = self._get_info()
            return self._info

        def _get_default(self, cls):
            return getattr(self.config, f'default_{cls._cls_type()}')

        def _set_default(self, cls, value):
            with suppress(cls._cls_config_not_found()):
                if self._get_default(cls) == value:
                    return
            setattr(self.config, f'default_{cls._cls_type()}', value)

        def _get_object(self, cls, name, info=None):
            return cls(name, self, info=info)

        def _get_default_object(self, cls):
            return self._get_object(cls, self._get_default(cls))

        def _subcommand_info_opts(self):
            with suppress(AttributeError):
                return self.parent._subcommand_info_opts()
            return []
    
        def _list_info(self, cls):
            return self.az_responselist(*cls._cls_list_info_cmd(), *self._info_opts())

        def _get_objects(self, cls):
            return [self._get_object(cls, cls._cls_info_id(info), info=info)
                    for info in self._list_info(cls)]

    for cls in subclasses:
        assert issubclass(cls, StandardAzObjectSubclass)
        setattr(StandardAzObject, f'default_{cls._cls_type()}',
                property(fget=partialmethod(StandardAzObject._get_default, cls),
                         fset=partialmethod(StandardAzObject._set_default, cls)))
        setattr(StandardAzObject, f'get_{cls._cls_type()}',
                partialmethod(StandardAzObject._get_object, cls))
        setattr(StandardAzObject, f'get_default_{cls._cls_type()}',
                partialmethod(StandardAzObject._get_default_object, cls))
        setattr(StandardAzObject, f'get_{cls._cls_type()}s',
                partialmethod(StandardAzObject._get_objects, cls))

    return StandardAzObject
