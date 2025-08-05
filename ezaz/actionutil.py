
from abc import ABC
from abc import abstractmethod
from contextlib import suppress

from .argutil import ArgMap
from .response import Response
from .response import ResponseList


class ActionConfig:
    def __init__(self, action, *, aliases=[], handler, cmd=None, description='', argconfigs=[], az=None):
        self.action = action
        self.handler = handler
        self.cmd = cmd
        self.aliases = aliases
        self.description = description
        self.argconfigs = argconfigs
        self.az = az

    def __repr__(self):
        return f"{self.__class__.__name__}({self.action}, aliases={self.aliases}, handler={self.handler}, cmd={self.cmd}, description={self.description}, argconfigs={self.argconfigs}, az={self.az})"

    def handle(self, *args, **kwargs):
        return self._response(self.handler(*args, **kwargs))

    def _response(self, response):
        if response is None:
            return NoResponseHandler(response)
        if isinstance(response, Response):
            return ResponseHandler(response)
        if isinstance(response, ResponseList):
            return ResponseListHandler(response)
        if isinstance(response, str):
            return ResponseTextHandler(response)
        return UnknownResponseHandler(response)

    def is_action(self, action):
        return action in ([self.action] + self.aliases)

    @property
    def summary(self):
        s = self.action
        if self.aliases:
            s += f' ({','.join(self.aliases)})'
        if self.description:
            s += f': {self.description}'
        return s

    def add_to_parser(self, parser):
        for argconfig in self.argconfigs:
            argconfig.add_to_parser(parser)
        parser.set_defaults(actioncfg=self)

    def cmd_args(self, **opts):
        return ArgMap(*map(lambda argconfig: argconfig.cmd_args(**opts), self.argconfigs))


class ActionHandler(ABC):
    def __init__(self, func):
        self.func = func

    @abstractmethod
    def __call__(self, command, **opts):
        pass


class ResponseHandler:
    def __init__(self, response):
        self.response = response

    def _print(self, response):
        try:
            print(response.name)
        except AttributeError:
            print(response.id)

    def print(self):
        self._print(self.response)

    def _print_verbose(self, response):
        print(response)

    def print_verbose(self):
        self._print_verbose(self.response)


class ResponseListHandler(ResponseHandler):
    def print(self):
        for response in self.response:
            self._print(response)

    def print_verbose(self):
        for response in self.response:
            self._print_verbose(response)


class NoResponseHandler(ResponseHandler):
    def _print(self, response):
        pass


class ResponseTextHandler(ResponseHandler):
    def _print(self, response):
        print(response)


class UnknownResponseHandler(ResponseHandler):
    def _print(self, response):
        print(f'Unknown response: {response}')
