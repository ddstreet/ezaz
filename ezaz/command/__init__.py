
from pathlib import Path

from ..importclasses import SubclassImporter
from .command import SimpleCommand


COMMAND_CLASSES = SubclassImporter(Path(__file__).parent, __name__, SimpleCommand, ['__init__.py', 'command.py'], debug=False).subclasses
