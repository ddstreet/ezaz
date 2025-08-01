
from .account import AzObjectAccountCommand


class LoginCommand(AzObjectAccountCommand):
    @classmethod
    def command_name_list(cls):
        return ['login']

    def _run(self):
        self.azobject.do_action('login')

    def run(self):
        self.run_login()
