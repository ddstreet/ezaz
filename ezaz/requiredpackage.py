
import importlib
import shutil


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
        try:
            for m in self.modules:
                importlib.import_module(m)
        except ImportError:
            return False
        return True

    @property
    def is_available(self):
        return self.are_programs_available and self.are_modules_available
