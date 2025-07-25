
from functools import cached_property

from ..argutil import ArgMap
from ..argutil import YesBoolArgConfig
from ..config import Config
from ..dialog import YesNo
from .command import ActionCommand


class ConfigCommand(ActionCommand):
    @classmethod
    def command_name_list(cls):
        return ['config']

    @classmethod
    def get_action_configs(cls):
        return [*super().get_action_configs(),
                cls.make_action_config('show', description='Show configuration'),
                cls.make_action_config('remove', description='Remove configuration file', argconfigs=[YesBoolArgConfig()])]

    @cached_property
    def config(self):
        return Config(self.options.configfile)

    def show(self, **opts):
        print(self.config)

    def remove(self, **opts):
        if not self.config:
            print('There is no config to remove.')
        elif self.opts.get('yes') or YesNo('About to remove the configuration file, are you sure?'):
            if self.dry_run:
                print('DRY-RUN: not removing configuration file.')
            else:
                self.config.remove()
                print('Configuration file removed.')
        else:
            print('Configuration file not removed.')
