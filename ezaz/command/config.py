
from ..dialog import YesNo
from .command import ActionCommand
from .command import ActionParser


class ConfigCommand(ActionCommand):
    @classmethod
    def command_name_list(cls):
        return ['config']

    @classmethod
    def parser_get_action_parsers(cls):
        return (super().parser_get_action_parsers() +
                [ActionParser('show', description='Show configuration'),
                 ActionParser('remove', description='Remove configuration file')])

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
