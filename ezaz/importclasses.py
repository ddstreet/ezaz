
import importlib
import inspect

from contextlib import contextmanager
from pathlib import Path


class SubclassImporter:
    def __init__(self, module_path, module_name, superclass, ignore_files=[], debug=False):
        self.module_path = Path(module_path)
        self.module_name = module_name
        self.superclass = superclass
        self.ignore_files = ignore_files
        self._debug = debug
        self._indent = 0

        assert self.module_path.is_dir()
        assert inspect.isclass(superclass)

    @contextmanager
    def indent(self):
        self._indent += 2
        try:
            yield
        finally:
            self._indent -= 2

    def debug(self, msg, arrow=False):
        if self._debug:
            indent = ('>' if arrow else ' ') * self._indent
            print(f'{indent}{msg}')

    def conditional_debug(self, condition, msg, alt):
        self.debug(msg if condition else alt)
        return condition

    def is_py(self, f):
        return self.conditional_debug(f.suffix.lower() == '.py',
                                      f'File {f} is python file',
                                      f'File {f} is not python file, ignoring')

    def is_alpha(self, name):
        return self.conditional_debug(len(name) > 0 and name[0].isalpha(),
                                      f"Name '{name}' is ok",
                                      f"Name '{name}' does not start with character, ignoring")

    def is_not_ignore(self, f):
        return self.conditional_debug(f.name not in self.ignore_files,
                                      f'File {f} not in ignore files',
                                      f'File {f} in ignore files, ignoring')

    def is_file_ok(self, f):
        return self.is_py(f) and self.is_alpha(f.name) and self.is_not_ignore(f)

    def import_module(self, f):
        return importlib.import_module('.' + f.with_suffix('').name, self.module_name)

    @property
    def modules(self):
        for f in self.module_path.iterdir():
            with self.indent():
                if self.is_file_ok(f):
                    yield self.import_module(f)

    def is_class(self, k, v):
        return self.conditional_debug(inspect.isclass(v),
                                      f"Attr '{k}' value is a class",
                                      f"Attr '{k}' value is not a class, ignoring")
    
    def is_not_abstract(self, k, v):
        return (self.is_class(k, v) and
                self.conditional_debug(not inspect.isabstract(v),
                                       f"Attr '{k}' value is not abstract",
                                       f"Attr '{k}' value is abstract, ignoring"))
    
    def is_subclass(self, k, v):
        return (self.is_not_abstract(k, v) and
                self.conditional_debug(issubclass(v, self.superclass),
                                       f"Attr '{k}' value is a subclass of {self.superclass.__name__}",
                                       f"Attr '{k}' value is not a subclass of {self.superclass.__name__}, ignoring"))

    @property
    def _subclasses(self):
        self.debug(f'Starting module {self.module_name}')
        for m in self.modules:
            with self.indent():
                for k, v in vars(m).items():
                    if self.is_alpha(k):
                        with self.indent():
                            if self.is_subclass(k, v):
                                with self.indent():
                                    self.debug(f'Found subclass {v.__name__}', arrow=True)
                                    yield v
        self.debug(f'Finished module {self.module_name}')

    @property
    def subclasses(self):
        return list(set(self._subclasses))
