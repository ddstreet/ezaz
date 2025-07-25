
from pathlib import Path

from ..importclasses import import_classes


COMMAND_CLASSES = import_classes(module_path=Path(__file__).parent,
                                 module_name=__name__,
                                 attribute='EZAZ_COMMAND_CLASS',
                                 ignore_files=['__init__.py', 'command.py'],
                                 debug=False)
