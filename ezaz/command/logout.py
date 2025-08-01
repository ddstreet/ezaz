
from .account import AzObjectAccountCommand


class LogoutCommand(AzObjectAccountCommand):
    @classmethod
    def command_name_list(cls):
        return ['logout']

    def _run(self):
        self.azobject.do_action('logout')

    def run(self):
        self.run_logout()
