
from contextlib import suppress
from functools import cached_property

from ..argutil import ArgConfig
from ..argutil import AzClassDescendantsChoicesArgConfig
from ..argutil import BoolArgConfig
from ..argutil import ChoicesArgConfig
from ..argutil import ConstArgConfig
from ..argutil import ExclusiveGroupArgConfig
from ..config import Config
from ..exception import DefaultConfigNotFound
from ..exception import RequiredArgument
from ..exception import RequiredArgumentGroup
from ..filter import FILTER_TYPES
from ..filter import Filter
from .command import AzObjectActionCommand


class FiltersCommand(AzObjectActionCommand):
    @classmethod
    def command_name_list(cls):
        return ['filters']

    @classmethod
    def azclass(cls):
        from ..azobject.user import User
        return User

    @classmethod
    def get_action_configs(cls):
        return [cls.make_action_config('show',
                                       description='Show filter(s)',
                                       argconfigs=cls.get_show_action_argconfigs()),
                cls.make_action_config('add',
                                       description='Add filter',
                                       argconfigs=cls.get_add_action_argconfigs()),
                cls.make_action_config('remove',
                                       description='Remove filter(s)',
                                       argconfigs=cls.get_remove_action_argconfigs()),
                cls.make_action_config('clear',
                                       description='Remove all filter(s)',
                                       argconfigs=cls.get_clear_action_argconfigs())]

    @classmethod
    def get_show_action_argconfigs(cls):
        return [*cls.azclass().get_descendant_azobject_id_argconfigs()]

    @classmethod
    def get_azclass_descendants_argconfigs(cls):
        return AzClassDescendantsChoicesArgConfig('object_type',
                                                  dest='object_type',
                                                  azclass=cls.azclass(),
                                                  required=True,
                                                  help='The type of object to filter')

    @classmethod
    def get_add_action_argconfigs(cls):
        return [*cls.azclass().get_descendant_azobject_id_argconfigs(),
                cls.get_azclass_descendants_argconfigs(),
                ChoicesArgConfig('type',
                                 required=True,
                                 dest='filter_type',
                                 choices=FILTER_TYPES,
                                 help='Type of filter to add'),
                ArgConfig('field',
                          dest='filter_field',
                          help="Object field to filter (default is object 'id', which is the 'name' field for most objects)"),
                ArgConfig('value',
                          required=True,
                          dest='filter_value',
                          help='Filter value')]


    @classmethod
    def get_remove_action_argconfigs(cls):
        return [*cls.azclass().get_descendant_azobject_id_argconfigs(),
                cls.get_azclass_descendants_argconfigs(),
                ChoicesArgConfig('type',
                                 required=True,
                                 dest='filter_type',
                                 choices=FILTER_TYPES,
                                 help='Type of filter to remove'),
                ArgConfig('field',
                          dest='filter_field',
                          help="Object field to filter"),
                ArgConfig('value',
                          dest='filter_value',
                          help='Filter value')]

    @classmethod
    def get_clear_action_argconfigs(cls):
        return [*cls.azclass().get_descendant_azobject_id_argconfigs(),
                cls.get_azclass_descendants_argconfigs()]

    def _print_filters(self, parent, child_class, tab=''):
        filters = parent.get_child_filters(child_class.azobject_name())
        filter_text = f'filters: {filters}' if filters else 'has no filters'
        print(f'{tab}{parent.azobject_name()}({parent.azobject_id}) {child_class.azobject_text()} {filter_text}')

    def show(self, **opts):
        self._indent = 0
        self.show_azclass_filters(self.azclass(), opts)

    def show_azclass_filters(self, azclass, opts):
        if not azclass.get_child_classes():
            return

        azobject_id = azclass.get_azobject_id_from_opts(opts)
        if not azobject_id:
            try:
                azobject_id = azclass.get_default_azobject_id(**opts)
            except DefaultConfigNotFound:
                return

        print(f'{self.tab}{azclass.__name__}: {azobject_id}')
        no_filters = True
        for c in azclass.get_child_classes():
            filters = c.get_filters(**opts)
            if filters:
                no_filters = False
                print(f"{self.tab}>{c.__name__} filters: {filters}")
        if no_filters:
            print(f'{self.tab}>No filters')

        for child_class in azclass.get_child_classes():
            with self.indent():
                self.show_azclass_filters(child_class, opts)

    def add(self, object_type, filter_type, filter_value, filter_field=None, **opts):
        assert all((object_type, filter_type, filter_value))
        new_filter = Filter.create_filter(filter_type=filter_type, filter_value=filter_value, filter_field=filter_field)
        self.add_azclass_filter(self.azclass(), object_type, new_filter, opts)

    def add_azclass_filter(self, azclass, object_type, new_filter, opts):
        for child_class in azclass.get_child_classes():
            if child_class.azobject_name() == object_type:
                parent = azclass.get_instance(**opts)
                parent.add_child_filter(child_class.azobject_name(), new_filter)
                print(f'Added filter: {new_filter}')
                self._print_filters(parent, child_class)
                return True

            if self.add_azclass_filter(child_class, object_type, new_filter, opts):
                return True

        return False

    def remove(self, object_type, filter_type, filter_value, filter_field=None, **opts):
        assert all((object_type, filter_type, filter_value))
        old_filter = Filter.create_filter(filter_type=filter_type, filter_value=filter_value, filter_field=filter_field)
        self.remove_azclass_filter(self.azclass(), object_type, old_filter, opts)

    def remove_azclass_filter(self, azclass, object_type, old_filter, opts):
        for child_class in azclass.get_child_classes():
            if child_class.azobject_name() == object_type:
                parent = azclass.get_instance(**opts)
                old_filters = parent.get_child_filters(child_class.azobject_name())
                if old_filter not in old_filters:
                    print(f'Filter not found: {old_filter}')
                else:
                    parent.remove_child_filter(child_class.azobject_name(), old_filter)
                    print(f'Removed filter: {old_filter}')
                self._print_filters(parent, child_class)
                return True

            if self.remove_azclass_filter(child_class, object_type, old_filter, opts):
                return True

        return False

    def clear(self, object_type, **opts):
        self.clear_azclass_filters(self.azclass(), object_type, opts)

    def clear_azclass_filters(self, azclass, object_type, opts):
        for child_class in azclass.get_child_classes():
            if child_class.azobject_name() == object_type:
                parent = azclass.get_instance(**opts)
                parent.set_child_filters(child_class.azobject_name(), [])
                print(f'Removed all {azclass.__name__}({parent.azobject_id}) {child_class.azobject_text()} filters')
                filters = parent.get_child_filters(child_class.azobject_name())
                if filters:
                    raise RuntimeError(f'Filters remain after clearing all filters: {filters}')
                return True

            if self.clear_azclass_filters(child_class, object_type, opts):
                return True

        return False
