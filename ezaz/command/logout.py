
from .account import AccountCommand


class LogoutCommand(AccountCommand):
    @classmethod
    def command_name_list(cls):
        return ['logout']

    def _run(self):
        self.azobject.do_action('logout')

    def run(self):
        self.run_logout()
