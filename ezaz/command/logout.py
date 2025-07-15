
from .account import AccountCommand


class LogoutCommand(AccountCommand):
    @classmethod
    def command_name_list(cls):
        return ['logout']

    @classmethod
    def _parser_add_arguments(cls, parser):
        pass

    def _run(self):
        self.logout()
