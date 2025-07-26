
import os

from pathlib import Path

from .requiredpackage import RequiredPackage


DEFAULT_CONFIGPATH = Path(os.environ.get('XDG_CONFIG_HOME', '~/.config')) / 'ezaz'

REQUIRED_PACKAGES = [
    RequiredPackage('azure-cli', programs=['az']),
    RequiredPackage('argcomplete', modules=['argcomplete']),
    RequiredPackage('jsonschema', modules=['jsonschema']),
]
