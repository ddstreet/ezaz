
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
        resp = input('About to remove the configuration file, are you sure? (y/N)')
        if resp.lower() in ['y', 'yes']:
            self._config.remove()
            print('Configuration file removed.')
        else:
            print('Configuration file not removed.')
