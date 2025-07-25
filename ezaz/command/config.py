
from ..dialog import YesNo
from .command import ActionCommand


class ConfigCommand(ActionCommand):
    @classmethod
    def command_name_list(cls):
        return ['config']

    @classmethod
    def parser_add_action_arguments(cls, group):
        cls._parser_add_action_argument(group, '--show',
                                        help=f'Show config (default)')
        cls._parser_add_action_argument(group, '--remove',
                                        help=f'Remove config (caution, this removes all config!)')

    @classmethod
    def parser_set_action_default(cls, group):
        cls._parser_set_action_default(group, 'show')

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
