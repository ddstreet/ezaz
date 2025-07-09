
import ast
import os
import subprocess
import sys
import venv

from functools import cached_property
from pathlib import Path

from . import DEFAULT_CONFIGPATH
from . import REQUIRED_PKGS


DEFAULT_VENVDIR = DEFAULT_CONFIGPATH / 'venv'


class ImportVenv:
    def __init__(self, *, venvdir=DEFAULT_VENVDIR, packages=REQUIRED_PKGS, verbose=False, clear=False):
        self.venvdir = Path(venvdir).expanduser().absolute()
        self.verbose = verbose

        if not self.venvdir.is_dir() or clear:
            venv.create(str(self.venvdir), clear=clear, with_pip=True)

        # This assumes the package name can be directly converted to an import path
        # e.g. 'azure-identity' -> 'azure/identity'
        self.packages = []
        for package in packages:
            if not self.pythonpackagedir(package).is_dir():
                self.packages.append(package)

    @property
    def bindir(self):
        return self.venvdir / 'bin'

    @property
    def libdir(self):
        return self.venvdir / 'lib'

    @cached_property
    def sitepackagesdir(self):
        syspath = subprocess.run([str(self.bindir / 'python'), '-c' 'import sys; print(sys.path)'],
                                text=True, check=True, stdout=subprocess.PIPE).stdout
        paths = [p for p in ast.literal_eval(syspath) if p.startswith(str(self.libdir)) and p.endswith('site-packages')]
        if len(paths) < 1:
            raise FileNotFoundError('no venv python site-packages dir found')
        if len(paths) == 1:
            return Path(paths[0])
        if len(paths) > 2:
            raise RuntimeError('multiple venv python site-packages dirs found, try refreshing the venv')

    def pythonpackagedir(self, package):
        return self.sitepackagesdir / package.replace('-', '/')

    def __enter__(self):
        self.oldpath = os.environ['PATH']
        self.oldsyspath = sys.path

        os.environ['PATH'] = f"{self.bindir}:{os.environ['PATH']}"
        sys.path.append(str(self.sitepackagesdir))

        cmd = ['pip']
        if not self.verbose:
            cmd.append('-q')
        cmd.append('install')

        if self.packages:
            subprocess.run(cmd + self.packages, text=True, check=True)

    def __exit__(self, exc_type, exc_value, traceback):
        os.environ['PATH'] = self.oldpath
        sys.path = self.oldsyspath
