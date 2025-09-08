
import logging
import os

from pathlib import Path

from .requiredpackage import RequiredPackage


LOGGER = logging.getLogger(__name__)
AZ_LOGGER = logging.getLogger(f'{__name__}.AZ')
IMPORTCLASSES_LOGGER = logging.getLogger(f'{__name__}.IMPORTCLASSES')

DEFAULT_CONFIGPATH = Path(os.environ.get('XDG_CONFIG_HOME', '~/.config')) / 'ezaz'
DEFAULT_CACHEPATH = Path(os.environ.get('XDG_CACHE_HOME', '~/.cache')) / 'ezaz'

REQUIRED_PACKAGES = [
    RequiredPackage('azure-cli', programs=['az']),
    RequiredPackage('argcomplete', modules=['argcomplete']),
    RequiredPackage('cryptography', modules=['cryptography']),
    RequiredPackage('dateparser', modules=['dateparser']),
    RequiredPackage('jsonschema', modules=['jsonschema']),
]

DISTRO_IMAGES = {
    'azl3': 'MicrosoftCBLMariner:azure-linux-3:azure-linux-3-gen2:latest',
    'linuxguard': '/subscriptions/035db282-f1c8-4ce7-b78f-2a7265d5398c/resourceGroups/LinuxGuardPipelines/providers/Microsoft.Compute/galleries/linuxguardgallery/images/linuxguard-base/versions/latest',
    'ultraviolet': '/subscriptions/e8163038-eb55-4108-b164-1d0563f63588/resourceGroups/ddstreetwestus2rg/providers/Microsoft.Compute/galleries/ddstreetwestus2ig/images/ddstreetwestus2id/versions/latest',
    'ubuntu-22.04': 'Canonical:0001-com-ubuntu-server-jammy-daily:22_04-daily-lts-gen2:latest',
    'ubuntu-24.04': 'Canonical:ubuntu-24_04-lts-daily:server:latest',
    'ubuntu-lts': 'Canonical:ubuntu-24_04-lts-daily:server:latest',
    'ubuntu-25.04': 'Canonical:ubuntu-25_04-daily:server:latest',
    'ubuntu-25.10': 'Canonical:ubuntu-25_10-daily:server:latest',
    'opensuse-15.6': 'SUSE:opensuse-leap-15-6:gen2:latest',
    'sles-15.3': 'SUSE:sles-15-sp3:gen2:latest',
    'sles-15.4': 'SUSE:sles-15-sp4:gen2:latest',
    'sles-15.5': 'SUSE:sles-15-sp5:gen2:latest',
    'sles-15.6': 'SUSE:sles-15-sp6:gen2:latest',
    'sles-15.7': 'SUSE:sles-15-sp7:gen2:latest',
}
