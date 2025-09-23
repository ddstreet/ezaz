
from contextlib import suppress
from functools import cached_property

from .. import LOGGER
from ..argutil import BoolArgConfig
from ..config import Config
from ..exception import DefaultConfigNotFound
from .command import AzObjectActionCommand


class DefaultsCommand(AzObjectActionCommand):
    @classmethod
    def command_name_list(cls):
        return ['defaults']

    @classmethod
    def azclass(cls):
        from ..azobject.user import User
        return User

    @classmethod
    def get_action_configs(cls):
        return [cls.make_action_config('show',
                                       description='Show defaults',
                                       argconfigs=cls.get_show_action_argconfigs()),
                cls.make_action_config('set',
                                       description='Set defaults',
                                       argconfigs=cls.get_set_action_argconfigs()),
                cls.make_action_config('unset',
                                       description='Unset/remove defaults',
                                       argconfigs=cls.get_unset_action_argconfigs())]

    @classmethod
    def get_show_action_argconfigs(cls):
        return [BoolArgConfig('check', help='Check if the default id for each object type exists')]

    @classmethod
    def get_set_action_argconfigs(cls):
        return [*cls.azclass().get_descendant_azobject_id_argconfigs(help='Set the {azobject_text} default id'),
                BoolArgConfig('check', help='Check if the default id for each object type exists'),
                BoolArgConfig('force', help='Set the default id even if existence check failed')]

    @classmethod
    def get_unset_action_argconfigs(cls):
        return [BoolArgConfig(azclass.azobject_name(), help=f'Unset the {azclass.azobject_text()} default id')
                for azclass in cls.azclass().get_descendant_classes()]

    def show(self, *, check, **opts):
        self._indent = 0
        self.show_azclass(self.azclass(), check)

    def show_azclass(self, azclass, check):
        try:
            default_id = azclass.get_default_azobject_id()
        except DefaultConfigNotFound:
            return

        if check and not azclass.get_default_instance().exists():
            exists = ' (Does not exist)'
        else:
            exists = ''

        print(f'{self.tab}{azclass.__name__}: {default_id}{exists}')

        for subcls in azclass.get_child_classes():
            with self.indent():
                self.show_azclass(subcls, check)

    def set(self, *, check, force, **opts):
        self.set_azclass(self.azclass(), check, force, opts)

    def set_azclass(self, azclass, check, force, opts):
        try:
            current_id = azclass.get_default_azobject_id()
        except DefaultConfigNotFound:
            current_id = None

        new_id = azclass.get_azobject_id_from_opts(opts)
        LOGGER.debug(f'{azclass.__name__}({current_id}) -> ({new_id})')
        if new_id:
            current_id = self.set_azclass_default_id(azclass, current_id, new_id, check, force, opts)

        if not current_id:
            return

        for child_class in azclass.get_child_classes():
            self.set_azclass(child_class, check, force, opts)

    def set_azclass_default_id(self, azclass, current_id, new_id, check, force, opts):
        name = azclass.azobject_name()
        text = azclass.azobject_text()

        exists = not check or azclass.get_specific_instance(new_id).exists()
        exists_text = '' if exists else ' (which does not exist)'

        if current_id == new_id:
            print(f'Current {text} default id is already {new_id}{exists_text}')
            return current_id

        if not exists and not force:
            print(f'Refusing to set {text} default id to {new_id} because it does not exist')
            return current_id

        azclass.set_default_azobject_id(new_id, opts)
        if current_id:
            print(f'Changed {text} default id from {current_id} to {new_id}{exists_text}')
        else:
            print(f'Set {text} default id to {new_id}{exists_text}')

        return new_id

    def unset(self, **opts):
        self.unset_azclass(self.azclass(), opts)

    def unset_azclass(self, azclass, opts):
        name = azclass.azobject_name()
        text = azclass.azobject_text()

        try:
            default_id = azclass.get_default_azobject_id()
        except DefaultConfigNotFound:
            if opts.get(name):
                print(f'Already no {text} default id')
            return

        for child_class in azclass.get_child_classes():
            self.unset_azclass(child_class, opts)

        if opts.get(name):
            azclass.del_default_azobject_id()
            print(f'Removed {text} default id {default_id}')
