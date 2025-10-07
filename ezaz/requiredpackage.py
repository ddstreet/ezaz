
import importlib
import shutil


class VersionedModule:
    def __init__(self, name, version):
        self.name = name
        self.version = version


class RequiredPackage:
    def __init__(self, name, *, programs=[], modules=[]):
        self.name = name
        self.programs = programs
        self.modules = modules

    @property
    def are_programs_available(self):
        return all([shutil.which(p) for p in self.programs])

    @property
    def are_modules_available(self):
        return all((self.check_module(m) for m in self.modules))

    def check_module(self, module):
        if isinstance(module, VersionedModule):
            return self._check_module(module.name, module.version)
        return self._check_module(module)

    def _check_module(self, module, minversion=None):
        try:
            importlib.import_module(module)
        except ImportError:
            return False
        if minversion:
            from importlib import metadata
            return metadata.version(module) >= minversion
        return True

    @property
    def is_available(self):
        return self.are_programs_available and self.are_modules_available
