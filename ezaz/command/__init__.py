
from pathlib import Path

from ..importclasses import find_all_classes
from .command import SimpleCommand


COMMAND_CLASSES = find_all_classes(Path(__file__).parent,
                                   __name__,
                                   ['__init__.py', 'command.py'],
                                   SimpleCommand)
