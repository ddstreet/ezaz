
import argparse
import re
import string

from contextlib import suppress
from functools import partial


class SharedArgumentParser(argparse.ArgumentParser):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._shared_args = []

    def add_argument(self, *args, shared=False, **kwargs):
        if shared:
            self._shared_args.append(SharedArgument(*args, **kwargs))
        return super().add_argument(*args, **kwargs)

    def add_subparsers(self, *args, **kwargs):
        subparsers = super().add_subparsers(*args, **kwargs)
        subparsers.add_parser = partial(self._subparsers_add_parser, subparsers.add_parser)
        return subparsers

    def _subparsers_add_parser(self, add_parser, *args, **kwargs):
        parser = add_parser(*args, **kwargs)
        for p in self._shared_args:
            parser.add_argument(*p.args, **p.kwargs)
        parser._shared_args = self._shared_args
        return parser

    def parse_args(self, args):
        opts = super().parse_args(args)
        for p in self._shared_args:
            p.parse_shared_arg(args, opts)
        return opts


class SharedArgument:
    def __init__(self, *args, **kwargs):
        self.args = args
        self.kwargs = kwargs

    def parse_shared_arg(self, args, namespace):
        parser = argparse.ArgumentParser(add_help=False)
        parser.add_argument(*self.args, **self.kwargs)
        parser.add_argument(*[a for a in [f'-{l}' for l in string.ascii_letters] if a not in self.args],
                            action='store_true',
                            dest='__ignore')
        ns = parser.parse_known_args(args)[0]
        for k, v in vars(ns).items():
            if k != '__ignore':
                setattr(namespace, k, v)
