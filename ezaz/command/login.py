
from .account import AccountCommand


class LoginCommand(AccountCommand):
    @classmethod
    def name(cls):
        return 'login'

    @classmethod
    def _parser_add_arguments(cls, parser):
        parser.add_argument('--use-device-code',
                            action='store_true',
                            help='Instead of opening a browser window, show the URL and code')

    def _run(self):
        self.login()
