
from ..azobject.account import Account
from .account import AccountCommand
from .command import SimpleCommand


class LoginCommand(SimpleCommand):
    @classmethod
    def command_name_list(cls):
        return ['login']

    @classmethod
    def parser_add_common_arguments(cls, parser):
        super().parser_add_common_arguments(parser)
        parser.add_argument('--use-device-code',
                            action='store_true',
                            help='Instead of opening a browser window, show the URL and code')

    def _setup(self):
        super()._setup()
        self._account = Account(self._config, verbose=self.verbose, dry_run=self.dry_run)

    def run(self):
        AccountCommand.cls_login(self._account, self._options.use_device_code)
