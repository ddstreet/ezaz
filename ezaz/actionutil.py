
import inspect

from abc import ABC
from abc import abstractmethod
from contextlib import suppress

from .argutil import ArgMap
from .argutil import ArgUtil
from .response import Response
from .response import ResponseList
from .response import response_id


# TODO - redo this with ActionConfig being azobject-specific, and add command-specific wrapper and/or alt config
class ActionConfig(ArgUtil):
    def __init__(self, action, *, aliases=[], handler=None, cls=None, cmd=None, description='', argconfigs=[], az=None):
        self.action = action
        self.aliases = aliases
        self.handler = handler
        self.cls = cls
        self.cmd = cmd
        self.description = description
        self.argconfigs = argconfigs
        self.az = az

        if not cls and not handler:
            raise RuntimeError('Invalid ActionConfig, must provide cls or handler')

    def __repr__(self):
        return self.__class__.__name__ + '(' + (f"{self.action}, " +
                                                f"aliases={self.aliases}, " +
                                                f"handler={self.handler}, " +
                                                f"cls={self.cls}, " +
                                                f"cmd={self.cmd}, " +
                                                f"description={self.description}, " +
                                                f"argconfigs={self.argconfigs}, " +
                                                f"az={self.az})")

    def _handle(self, *, command, **kwargs):
        # TODO - need to think of better way to handle this, dispatch maybe
        if isinstance(command, self.cls):
            return getattr(command, self.action)(**kwargs)
        elif inspect.ismethod(getattr(command.azclass(), self.action)):
            return getattr(command.azclass(), self.action)(command.parent_azobject, **kwargs)
        elif isinstance(command.azobject, self.cls):
            return getattr(command.azobject, self.action)(**kwargs)
        else:
            raise RuntimeError('Invalid ActionConfig')

    def handle(self, **kwargs):
        if self.handler:
            return self._response(self.handler(**kwargs))
        elif self.cls:
            return self._response(self._handle(**kwargs))

    def _response(self, response):
        if response is None:
            return NoResponseHandler(response)
        if isinstance(response, Response):
            return ResponseHandler(response)
        if isinstance(response, (ResponseList, list)):
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
            s += f' ({",".join(self.aliases)})'
        if self.description:
            s += f': {self.description}'
        return s

    def add_to_parser(self, parser):
        for argconfig in self.argconfigs:
            argconfig.add_to_parser(parser)

    def cmd_args(self, **opts):
        return ArgMap(*map(lambda argconfig: argconfig.cmd_args(**opts), self.argconfigs))

    def get_arg_value(self, arg, **opts):
        opt = self._arg_to_opt(arg)
        return self.cmd_args(**{opt: opts.get(opt)}).get(self._opt_to_arg(opt))


class ResponseHandler:
    def __init__(self, response):
        self.response = response

    def _print(self, response):
        print(response_id(response))

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

    def _print_verbose(self, response):
        pass


class ResponseTextHandler(ResponseHandler):
    def _print(self, response):
        print(response)


class UnknownResponseHandler(ResponseHandler):
    def _print(self, response):
        print(f'Unknown response: {response}')
