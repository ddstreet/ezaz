
from functools import cached_property

from .. import LOG_V0
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
    def get_action_configmap(cls):
        return ArgMap(super().get_action_configmap(),
                      show=cls.make_action_config('show', description='Show configuration (default)'),
                      remove=cls.make_action_config('remove', description='Remove configuration file', argconfigs=[YesBoolArgConfig()]))

    @classmethod
    def get_default_action(cls):
        return 'show'

    @cached_property
    def config(self):
        return Config(self.options.configfile)

    def show(self, **opts):
        LOG_V0(self.config)

    def remove(self, **opts):
        if not self.config:
            LOG_V0('There is no config to remove.')
        elif self.opts.get('yes') or YesNo('About to remove the configuration file, are you sure?'):
            if self.dry_run:
                LOG_V0('DRY-RUN: not removing configuration file.')
            else:
                self.config.remove()
                LOG_V0('Configuration file removed.')
        else:
            LOG_V0('Configuration file not removed.')
