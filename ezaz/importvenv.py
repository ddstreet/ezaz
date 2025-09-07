
import ast
import os
import subprocess
import sys
import venv

from functools import cached_property
from pathlib import Path

from . import DEFAULT_CONFIGPATH
from . import REQUIRED_PACKAGES


DEFAULT_VENVDIR = DEFAULT_CONFIGPATH / 'venv'


class ImportVenv:
    def __init__(self, *, venvdir=DEFAULT_VENVDIR, required_packages=REQUIRED_PACKAGES, debug=False, refresh=False):
        self.venvdir = Path(venvdir).expanduser().resolve()
        self.debug = debug
        self.system_packages = []
        self.venv_packages = []

        # Skip everything for argcomplete
        if '_ARGCOMPLETE' in os.environ.keys():
            return

        if self.need_refresh(refresh):
            # We want to be verbose during initial creation (usually first run of ezaz), or during a refresh
            self.debug = True
            recreated = 'recreated' if self.venvdir.is_dir() else 'created'
            self.log(f'Virtual environment needs to be {recreated}, please wait...', end='', flush=True)
            venv.create(str(self.venvdir), clear=refresh, with_pip=True)
            self.log('done.')

        for p in required_packages:
            if p.is_available:
                self.log(f'Using system version of package {p.name}')
                self.system_packages.append(p)
            else:
                self.venv_packages.append(p)

    def need_refresh(self, refresh):
        return (refresh or
                not self.venvdir.is_dir() or
                not self.venvdir.joinpath('bin').joinpath('pip').exists() or
                not self.venvdir.joinpath('bin').joinpath('python').exists())

    def log(self, *args, **kwargs):
        if self.debug:
            # We use print because we haven't set up logging yet
            print(*args, **kwargs)

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
            raise RuntimeError('multiple venv python site-packages dirs found, try refreshing the venv with --refresh-venv')

    def pythonpackagedir(self, package):
        return self.sitepackagesdir / package.replace('-', '/')

    def run_pip(self, package):
        # We explicitly print everything here, as it might take a while
        print(f'Installing package in virtual environment: {package}')
        process = subprocess.Popen(['pip', 'install', '-v', package], stdout=subprocess.PIPE, bufsize=1, text=True)

        max_line_len = os.get_terminal_size().columns - 1
        last_linelen = 0
        while process.poll() is None:
            line = process.stdout.readline().rstrip()
            print('\r' + ' ' * last_linelen + '\r', end='')
            if len(line) > max_line_len:
                line = line[:max_line_len-3] + '...'
            last_linelen = len(line)
            print(line, end='', flush=True)

    def __enter__(self):
        self.oldpath = os.environ['PATH']
        self.oldsyspath = sys.path

        os.environ['PATH'] = f"{self.bindir}:{os.environ['PATH']}"
        sys.path.append(str(self.sitepackagesdir))

        missing_packages = []
        for p in self.venv_packages:
            if p.is_available:
                self.log(f'Using venv version of package {p.name}')
            else:
                missing_packages.append(p)

        for p in missing_packages:
            self.run_pip(p.name)

        return self

    def __exit__(self, exc_type, exc_value, traceback):
        os.environ['PATH'] = self.oldpath
        sys.path = self.oldsyspath
