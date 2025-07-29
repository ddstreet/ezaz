
from ..dialog import YesNo
from .command import ActionCommand
from .command import ActionParserConfig


class ConfigCommand(ActionCommand):
    @classmethod
    def command_name_list(cls):
        return ['config']

    @classmethod
    def parser_get_action_parser_configs(cls):
        return (super().parser_get_action_parser_configs() +
                [ActionParserConfig('show', description='Show configuration'),
                 ActionParserConfig('remove', description='Remove configuration file')])

    @classmethod
    def parser_get_action_default(cls):
        return 'show'

    def show(self):
        print(self._config)

    def remove(self):
        if not self._config:
            print('There is no config to remove.')
        elif YesNo('About to remove the configuration file, are you sure?'):
            self._config.remove()
            print('Configuration file removed.')
        else:
            print('Configuration file not removed.')
