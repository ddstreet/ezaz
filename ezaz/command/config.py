
from ..argutil import ActionConfig
from ..argutil import ArgMap
from ..dialog import YesNo
from .command import ActionCommand


class ConfigCommand(ActionCommand):
    @classmethod
    def command_name_list(cls):
        return ['config']

    @classmethod
    def get_action_configmap(cls):
        return ArgMap(super().get_action_configmap(),
                      show=cls.get_show_action_config(),
                      remove=cls.get_remove_action_config())

    @classmethod
    def get_show_action_config(cls):
        return ActionConfig('show', cmdobjmethod='show', description='Show configuration')

    @classmethod
    def get_remove_action_config(cls):
        return ActionConfig('remove', cmdobjmethod='remove', description='Remove configuration file')

    @classmethod
    def get_default_action(cls):
        return 'show'

    def show(self, action, opts):
        print(self.config)

    def remove(self, action, opts):
        if not self.config:
            print('There is no config to remove.')
        elif YesNo('About to remove the configuration file, are you sure?'):
            if self.dry_run:
                print('DRY-RUN: not removing configuration file.')
            else:
                self.config.remove()
            print('Configuration file removed.')
        else:
            print('Configuration file not removed.')
