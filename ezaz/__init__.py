
import os

from pathlib import Path

from .requiredpackage import RequiredPackage


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
    'lg': '/subscriptions/035db282-f1c8-4ce7-b78f-2a7265d5398c/resourceGroups/LinuxGuardPipelines/providers/Microsoft.Compute/galleries/linuxguardgallery/images/linuxguard-base/versions/latest',
    'uv': '/subscriptions/e8163038-eb55-4108-b164-1d0563f63588/resourceGroups/ddstreetwestus2rg/providers/Microsoft.Compute/galleries/ddstreetwestus2ig/images/ddstreetwestus2id/versions/latest',
    'ubuntu2204': 'Canonical:0001-com-ubuntu-server-jammy-daily:22_04-daily-lts-gen2:latest',
    'ubuntu2404': 'Canonical:ubuntu-24_04-lts-daily:server:latest',
    'ubuntults': 'Canonical:ubuntu-24_04-lts-daily:server:latest',
    'ubuntu2504': 'Canonical:ubuntu-25_04-daily:server:latest',
    'ubuntu2510': 'Canonical:ubuntu-25_10-daily:server:latest',
}
