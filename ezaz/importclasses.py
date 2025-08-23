
import importlib
import inspect

from contextlib import contextmanager
from pathlib import Path


def import_classes(**kwargs):
    return SubclassImporter(**kwargs).subclasses


# This returns non-abstract classes that are a subclass of the
# provided superclass OR have a (class) attribute with the provided
# name that is truthy.
class SubclassImporter:
    def __init__(self, *, module_path, module_name, superclass=None, attribute=None, ignore_files=[]):
        self.module_path = Path(module_path)
        self.module_name = module_name
        self.superclass = superclass
        self.attribute = attribute
        self.ignore_files = ignore_files
        self._indent = 0

        assert self.module_path.is_dir()
        if self.superclass:
            assert inspect.isclass(self.superclass)
        if self.attribute:
            assert isinstance(self.attribute, str)

    @contextmanager
    def indent(self):
        self._indent += 2
        try:
            yield
        finally:
            self._indent -= 2

    def debug(self, msg, arrow=False):
        import logging
        from . import LOGGER
        if LOGGER.isEnabledFor(logging.DEBUG):
            indent = ('>' if arrow else ' ') * self._indent
            LOGGER.debug(f'{indent}{msg}')

    def conditional_debug(self, condition, msg, alt):
        self.debug(msg if condition else alt)
        return condition

    def is_py(self, f):
        return self.conditional_debug(f.suffix.lower() == '.py',
                                      f'Using    {f} (is python file)',
                                      f'Ignoring {f} (is not python file)')

    def is_alpha(self, name):
        return self.conditional_debug(len(name) > 0 and name[0].isalpha(),
                                      f"Using    {name} (valid name)",
                                      f"Ignoring {name} (invalid name)")

    def is_not_ignore(self, f):
        return self.conditional_debug(f.name not in self.ignore_files,
                                      f'Using    {f} (not in ignore files)',
                                      f'Ignoring {f} (in ignore files)')

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

    def is_key_ok(self, k):
        return self.is_alpha(k)

    @property
    def items(self):
        for m in self.modules:
            with self.indent():
                for k, v in vars(m).items():
                    if self.is_key_ok(k):
                        yield k, v

    def is_class(self, k, v):
        return self.conditional_debug(inspect.isclass(v),
                                      f"Using    {k} (is a class)",
                                      f"Ignoring {k} (not a class)")

    def is_not_abstract(self, k, v):
        return (self.is_class(k, v) and
                self.conditional_debug(not inspect.isabstract(v),
                                       f"Using    {k} (is not abstract)",
                                       f"Ignoring {k} (is abstract)"))

    def is_subclass(self, k, v):
        return (self.superclass and
                self.is_not_abstract(k, v) and
                self.conditional_debug(issubclass(v, self.superclass),
                                       f"Using    {k} (is subclass of {self.superclass.__name__})",
                                       f"Ignoring {k} (is not subclass of {self.superclass.__name__})"))

    def is_attribute_truthy(self, k, v):
        return (self.attribute and
                self.conditional_debug(getattr(v, self.attribute, False),
                                       f"Using    {k} (its attribute {self.attribute} is truthy)",
                                       f"Ignoring {k} (its attribute {self.attribute} is not truthy)"))

    @property
    def classes(self):
        for k, v in self.items:
            with self.indent():
                if (self.is_attribute_truthy(k, v) and self.is_not_abstract(k, v)) or self.is_subclass(k, v):
                    yield v

    @property
    def _subclasses(self):
        self.debug(f'Starting module {self.module_name}')
        for c in self.classes:
            with self.indent():
                self.debug(f'Using class {c.__name__}', arrow=True)
                yield c
        self.debug(f'Finished module {self.module_name}')

    @property
    def subclasses(self):
        # Filter out duplicates
        return list(set(self._subclasses))
