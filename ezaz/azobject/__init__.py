
from pathlib import Path

from ..importclasses import SubclassImporter
from .azobject import AzObject


AZOBJECT_CLASSES = SubclassImporter(Path(__file__).parent, __name__, AzObject, ['__init__.py', 'azobject.py'], debug=False).subclasses

