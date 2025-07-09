
from .account import AccountCommand


class LogoutCommand(AccountCommand):
    @classmethod
    def name(cls):
        return 'logout'

    @classmethod
    def _parser_add_arguments(cls, parser):
        pass

    def run(self):
        self.logout()
