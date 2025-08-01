
from abc import abstractmethod

from ..azobject.account import Account
from ..exception import AlreadyLoggedIn
from ..exception import AlreadyLoggedOut
from ..exception import NotLoggedIn
from .command import AzObjectCommand
from .command import FilterActionCommand
from .command import ShowActionCommand


class AzObjectAccountCommand(AzObjectCommand):
    @classmethod
    def azclass(cls):
        return Account

    def run_show(self, already=False):
        logged = 'Already logged' if already else 'Logged'
        try:
            info = self.azobject.info
            print(f"{logged} in as '{info.user.name}' using subscription '{info.name}' (id {info.id})")
        except NotLoggedIn:
            print(f"{logged} out")

    def run_login(self):
        already = False
        try:
            self._run()
        except AlreadyLoggedIn:
            already = True
        self.run_show(already=already)

    def run_relogin(self):
        self._run()
        self.run_show()

    def run_logout(self):
        already = False
        try:
            self._run()
        except AlreadyLoggedOut:
            already = True
        self.run_show(already=already)

    @abstractmethod
    def _run(self):
        pass

    @abstractmethod
    def run(self):
        pass


class AccountCommand(FilterActionCommand, ShowActionCommand, AzObjectAccountCommand):
    pass
