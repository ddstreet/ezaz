
from ..argutil import ArgConfig
from ..dialog import YesNo
from .command import ActionCommand


class ConfigCommand(ActionCommand):
    @classmethod
    def command_name_list(cls):
        return ['config']

    @classmethod
    def parser_get_action_names(cls):
        return super().parser_get_action_names() + ['remove']

    @classmethod
    def parser_get_show_action_description(cls):
        return 'Show configuration'

    @classmethod
    def parser_get_remove_action_config(cls):
        return ArgConfig('remove', description='Remove configuration file')

    def do_show(self):
        print(self._config)

    def do_remove(self):
        if not self._config:
            print('There is no config to remove.')
        elif YesNo('About to remove the configuration file, are you sure?'):
            self._config.remove()
            print('Configuration file removed.')
        else:
            print('Configuration file not removed.')
