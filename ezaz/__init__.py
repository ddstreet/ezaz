
import logging
import time
import os

from pathlib import Path

from .requiredpackage import RequiredPackage
from .requiredpackage import VersionedModule


IS_ARGCOMPLETE = '_ARGCOMPLETE' in os.environ.keys()
ARGCOMPLETE_ARGS = (os.environ.get('COMP_LINE') or '').split()

LOGGER = logging.getLogger(__name__)
AZ_LOGGER = logging.getLogger(f'{__name__}.AZ')
IMPORTCLASSES_LOGGER = logging.getLogger(f'{__name__}.IMPORTCLASSES')

DEFAULT_CONFIGPATH = Path(os.environ.get('XDG_CONFIG_HOME', '~/.config')).joinpath('ezaz').expanduser().resolve()
DEFAULT_CONFIGFILE = 'config.json'

DEFAULT_CACHEPATH = Path(os.environ.get('XDG_CACHE_HOME', '~/.cache')).joinpath('ezaz').expanduser().resolve()

REQUIRED_PACKAGES = [
    RequiredPackage('azure-cli', programs=['az']),
    RequiredPackage('argcomplete', modules=[VersionedModule('argcomplete', '3')]),
    RequiredPackage('cryptography', modules=['cryptography']),
    RequiredPackage('dateparser', modules=['dateparser']),
    RequiredPackage('jmespath', modules=['jmespath']),
    RequiredPackage('jsonschema', modules=['jsonschema']),
]

LOGIN_REQUIRED_MESSAGES = [
    "az login",
    "has expired due to inactivity",
    "Interactive authentication is needed",
    "InteractionRequired",
]

DISTRO_IMAGES = {
    # x86
    'azl3': 'MicrosoftCBLMariner:azure-linux-3:azure-linux-3-gen2:latest',
    'opensuse-15.6': 'SUSE:opensuse-leap-15-6:gen2:latest',
    'rhel-10.0': 'RedHat:rhel-raw:100-raw-gen2:latest',
    'rhel-10.1': 'RedHat:rhel-raw:101-raw-gen2:latest',
    'sles-15.7': 'SUSE:sles-15-sp7:gen2:latest',
    'sles-16.0': 'SUSE:sles-16-0-x86-64:gen2:latest',
    'ubuntu-22.04': 'canonical:ubuntu-22_04-lts:server:latest',
    'ubuntu-24.04': 'canonical:ubuntu-24_04-lts:server:latest',
    'ubuntu-25.10': 'canonical:ubuntu-25_10:server:latest',
    'ubuntu-26.04': 'canonical:ubuntu-26_04-lts-daily:server:latest',
    'ubuntu-lts': 'Canonical:ubuntu-24_04-lts:server:latest',
    # Arm
    'azl3-arm': 'MicrosoftCBLMariner:azure-linux-3:azure-linux-3-arm64:latest',
    'opensuse-15.6-arm': 'SUSE:opensuse-leap-15-6-arm64:gen2:latest',
    'rhel-10.0-arm': 'RedHat:rhel-arm64:10_0-arm64:latest',
    'rhel-10.1-arm': 'RedHat:rhel-arm64:10_1-arm64:latest',
    'sles-15.7-arm': 'SUSE:sles-15-sp7-arm64:gen2:latest',
    'sles-16.0-arm': 'SUSE:sles-16-0-arm64:gen2:latest',
    'ubuntu-22.04-arm': 'canonical:ubuntu-22_04-lts:server-arm64:latest',
    'ubuntu-24.04-arm': 'canonical:ubuntu-24_04-lts:server-arm64:latest',
    'ubuntu-25.10-arm': 'canonical:ubuntu-25_10:server-arm64:latest',
    'ubuntu-26.04-arm': 'canonical:ubuntu-26_04-lts-daily:server-arm64:latest',
    'ubuntu-lts-arm': 'Canonical:ubuntu-24_04-lts:server-arm64:latest',
}


'''Return safely quoted content string. If content is empty string or None, it is returned unchanged.'''
def quote(content):
    import urllib.parse
    return urllib.parse.quote_plus(content) if content else content
