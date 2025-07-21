
from pathlib import Path

from ..importclasses import find_all_classes
from .azobject import AzObject


AZOBJECT_CLASSES = find_all_classes(Path(__file__).parent,
                                    __name__,
                                    ['__init__.py', 'azobject.py'],
                                    AzObject)
