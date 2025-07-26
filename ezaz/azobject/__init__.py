
from pathlib import Path

from ..importclasses import import_classes


AZOBJECT_CLASSES = import_classes(module_path=Path(__file__).parent,
                                  module_name=__name__,
                                  attribute='EZAZ_AZOBJECT_CLASS',
                                  ignore_files=['__init__.py', 'azobject.py'],
                                  debug=False)

