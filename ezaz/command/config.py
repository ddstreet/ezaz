
from .command import ActionCommand


class ConfigCommand(ActionCommand):
    @classmethod
    def command_name_list(cls):
        return ['config']

    @classmethod
    def parser_add_action_arguments(cls, group):
        cls.parser_add_action_argument_show(group)

    @classmethod
    def parser_add_action_argument_show(cls, group):
        cls._parser_add_action_argument(group, '--show',
                                        help=f'Show config (default)')

    @classmethod
    def parser_set_action_default(cls, group):
        cls._parser_set_action_default(group, 'show')

    def show(self):
        print(self._config)
