
from abc import abstractmethod
from collections import defaultdict
from contextlib import suppress

from .. import IS_ARGCOMPLETE
from .. import LOGGER
from ..argutil import ArgConfig
from ..argutil import AzObjectCompleter
from ..argutil import BoolArgConfig
from ..argutil import FlagArgConfig
from ..exception import InvalidFilter
from ..exception import TooLongForArgcomplete
from ..filter import Filter
from ..filter import RegexFilter
from ..schema import *
from .azobject import AzEmulateShowable
from .azobject import AzListable
from .azobject import AzSubObject
from .info import Info


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
                FlagArgConfig('all', # Need to use this to get full list for cacheing
                              default=True,
                              hidden=True),
                BoolArgConfig('include_unavailable', # This is only used for manual filtering
                              noncmd=True,
                              help=f'Include {cls.azobject_text()} that are unavailable in this subscription')]

    @classmethod
    def get_list_action_filter_group_argconfigs(cls):
        return [*super().get_list_action_filter_group_argconfigs(),
                ArgConfig('filter_capability',
                          dest='capability',
                          multiple=True,
                          noncmd=True,
                          completer=CapabilityCompleter(azclass=cls),
                          help=f'List only {cls.azobject_text()}s that exactly match the capability'),
                ArgConfig('filter_capability_list_item',
                          dest='capability_list_item',
                          multiple=True,
                          noncmd=True,
                          completer=CapabilityCompleter(azclass=cls),
                          help=f'List only {cls.azobject_text()}s that exactly match the capability as one of (or the only) item in a comma-separated list'),
                ArgConfig('filter_capability_regex',
                          dest='capability_regex',
                          multiple=True,
                          noncmd=True,
                          completer=CapabilityCompleter(azclass=cls),
                          help=f'List only {cls.azobject_text()}s that regex match the capability')]

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
    def get_capabilities_infolist(cls, infolist, verbose=0):
        caps = defaultdict(list)
        for info in infolist:
            for c in getattr(info, 'capabilities', []):
                caps[c.name].append(c.value)
        return [CapabilityInfo({'name': name, 'values': list(set(values))}, verbose=verbose)
                for name, values in caps.items()]

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
        if IS_ARGCOMPLETE and opts.get('_capabilities'):
            return super().list_read_cache(opts, tag='capabilities')
        infolist = super().list_read_cache(opts, tag='available')
        if opts.get('include_unavailable'):
            infolist.extend(super().list_read_cache(opts, tag='unavailable'))
        return infolist

    def list_pre(self, opts):
        result = super().list_pre(opts)
        if result is None:
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
            capabilities_infolist = self.get_capabilities_infolist(resource_infolist, verbose=self.verbose)
            resource_instance = self.parent.get_null_child(resource_class.azobject_name())
            resource_instance.list_write_cache_available(available_infolist)
            resource_instance.list_write_cache_unavailable(unavailable_infolist)
            resource_instance.list_write_cache_capabilities(capabilities_infolist)

    def list_write_cache_available(self, infolist):
        super().list_write_cache(infolist, tag='available')

    def list_write_cache_unavailable(self, infolist):
        super().list_write_cache(infolist, tag='unavailable')

    def list_write_cache_capabilities(self, infolist):
        super().list_write_cache(infolist, tag='capabilities')

    def list_filters(self, opts):
        if IS_ARGCOMPLETE and opts.get('_capabilities'):
            # No filters when getting cached capabilities, which are used only for shell completion
            return []
        return [*super().list_filters(opts),
                *(CapabilityEqualFilter(c) for c in opts.get('capability') or []),
                *(CapabilityListItemFilter(c) for c in opts.get('capability_list_item') or []),
                *(CapabilityRegexFilter(c) for c in opts.get('capability_regex') or [])]


class CapabilityFilter(Filter):
    def __init__(self, capability, *, filter_type):
        if '=' not in capability:
            raise InvalidFilter("Capability filter requires 'field=value' format")
        field, _, value = capability.partition('=')
        super().__init__(filter_type=filter_type, filter_field=field, filter_value=value)

    def _get_field_value(self, info):
        with suppress(AttributeError):
            for c in info.capabilities:
                if c.name == self.field:
                    return c.value
        return None


class CapabilityEqualFilter(CapabilityFilter):
    def __init__(self, capability, *, filter_type='capability_equal'):
        super().__init__(capability, filter_type=filter_type)

    def _check_value(self, value):
        return value == self.value


class CapabilityListItemFilter(CapabilityFilter):
    def __init__(self, capability, *, filter_type='capability_list_item'):
        super().__init__(capability, filter_type=filter_type)
        if ',' in self.value:
            raise InvalidFilter(f"Capability list-item value cannot contain comma: {self.value}")

    def _check_value(self, value):
        values = value.split(',')
        return self.value in values


class CapabilityRegexFilter(CapabilityFilter, RegexFilter):
    def __init__(self, capability, *, filter_type='capability_regex'):
        super().__init__(capability, filter_type=filter_type)


class CapabilityInfo(Info):
    _schema = OBJ(
        name=STR,
    )


class CapabilityCompleter(AzObjectCompleter):
    def get_info_list(self, opts):
        return super().get_info_list(opts | dict(_capabilities=True))

    def get_azobject_completer_choices(self, opts, prefix):
        infolist = self.get_info_list(opts)
        name, eq, value = prefix.partition('=')

        if not eq:
            # Completing the name
            return [f'{info.name}=' for info in infolist if info.name.startswith(name)]
        else:
            # Completing the value
            for info in infolist:
                if info.name == name:
                    return [f'{info.name}={v}' for v in info.values if v.startswith(value)]
            # No matches
            return []
