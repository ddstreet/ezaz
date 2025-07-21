
import importlib
import inspect

from pathlib import Path



def find_all_classes(module_path, module_name, ignore_files, superclass):
    classes = set()
    for f in Path(module_path).iterdir():
        if f.suffix.lower() == '.py' and f.name not in ignore_files:
            for k, v in vars(importlib.import_module('.' + f.with_suffix('').name, module_name)).items():
                if not k.startswith('_') and not inspect.isabstract(v) and inspect.isclass(v) and issubclass(v, superclass):
                    classes.add(v)
    return list(classes)
