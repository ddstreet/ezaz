
import os

from pathlib import Path


DEFAULT_CONFIGPATH = Path(os.environ.get('XDG_CONFIG_HOME', '~/.config')) / 'ezaz'

REQUIRED_PKGS = [
    'azure-cli',
    'jsonschema',
]
