
from abc import abstractmethod
from collections import defaultdict

from .. import IS_ARGCOMPLETE
from .. import LOGGER
from ..argutil import BoolArgConfig
from ..argutil import FlagArgConfig
from ..exception import TooLongForArgcomplete
from .azobject import AzEmulateShowable
from .azobject import AzListable
from .azobject import AzSubObject


class ComputeSku(AzEmulateShowable, AzListable, AzSubObject):
    @classmethod
    def get_cmd_base(cls):
        return ['vm']

    @classmethod
    def get_parent_class(cls):
        from .location import Location
        return Location

    @classmethod
    def get_list_action_cmd(cls):
        return cls.get_cmd_base() + ['list-skus']

    @classmethod
    def get_list_action_argconfigs(cls):
        return [*super().get_list_action_argconfigs(),
                FlagArgConfig('all',
                              default=True,
                              hidden=True),
                BoolArgConfig('include_unavailable',
                              noncmd=True,
                              help=f'Include {cls.azobject_text()} that are unavailable in this subscription')]

    @classmethod
    @abstractmethod
    def get_resource_type(cls):
        pass

    @classmethod
    def get_resource_type_class(cls, resource_type):
        for c in cls.get_parent_class().get_child_classes():
            if getattr(c, 'get_resource_type', lambda: None)() == resource_type:
                return c
        return None

    @classmethod
    def sort_by_resource_type(self, infolist):
        infolists = defaultdict(list)
        for info in infolist:
            infolists[info.resourceType].append(info)
        return infolists

    @classmethod
    def sort_by_availability(self, infolist):
        infolists = defaultdict(list)
        for info in infolist:
            for restriction in getattr(info, 'restrictions', []):
                if getattr(restriction, 'reasonCode', None) == 'NotAvailableForSubscription':
                    infolists['unavailable'].append(info)
                    break
            else:
                infolists['available'].append(info)
        return (infolists['available'], infolists['unavailable'])

    @classmethod
    def get_capability_infogetter(cls, capability):
        def get_info_capability(info):
            for c in info.capabilities:
                if c.name == capability:
                    return c.value
            return None

        return get_info_capability

    def id_list_read_cache(self, opts):
        idlist = super().id_list_read_cache(opts, tag='available')
        if opts.get('include_unavailable'):
            idlist.extend(super().id_list_read_cache(opts, tag='unavailable'))
        return idlist

    def list_read_cache(self, opts):
        infolist = super().list_read_cache(opts, tag='available')
        if opts.get('include_unavailable'):
            infolist.extend(super().list_read_cache(opts, tag='unavailable'))
        return infolist

    def list_pre(self, opts):
        result = super().list_pre(opts)
        if not result:
            if IS_ARGCOMPLETE:
                raise TooLongForArgcomplete(self.azobject_short_name(), 'list')
            LOGGER.warning('This command takes a long time, please be patient...')
        return result

    def list_write_cache(self, infolist):
        for resource_type, resource_infolist in self.sort_by_resource_type(infolist).items():
            resource_class = self.get_resource_type_class(resource_type)
            if not resource_class:
                LOGGER.warning(f"Unknown resource type '{resource_type}', ignoring")
                continue

            available_infolist, unavailable_infolist = self.sort_by_availability(resource_infolist)
            resource_instance = self.parent.get_null_child(resource_class.azobject_name())
            resource_instance.list_write_cache_available(available_infolist)
            resource_instance.list_write_cache_unavailable(unavailable_infolist)

    def list_write_cache_available(self, infolist):
        super().list_write_cache(infolist, tag='available')

    def list_write_cache_unavailable(self, infolist):
        super().list_write_cache(infolist, tag='unavailable')
