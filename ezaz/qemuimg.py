
import json
import shutil
import subprocess
import tempfile

from functools import cached_property
from pathlib import Path

from . import LOGGER
from .exception import ImageConversionFailed
from .exception import ImageError
from .exception import RequiredCommand
from .exception import UnknownImageFormat


class QemuImg:
    # The 'raw' format needs to be last, as it could match some other
    # formats (e.g. fixed vhd)
    FORMATS = ['vpc', 'vhdx', 'qcow2', 'qcow', 'vdi', 'vmdk', 'raw']

    def __init__(self, filename, dry_run=False):
        # Wrap filename with str() so we can accept str or Path types
        self.filename = str(filename)
        self.dry_run = dry_run
        if not self.filepath.exists():
            raise ImageError(f"Image file '{filename}' not found")

    @cached_property
    def filepath(self):
        return Path(self.filename)

    def _log_dry_run(self, msg):
        LOGGER.warning(f'DRY-RUN (not running): {msg}')

    def _which_cmd(self, cmdname):
        cmd = shutil.which(cmdname)
        if not cmd:
            raise RequiredCommand(f"Required program '{cmdname}' not found")
        return cmd

    @cached_property
    def _cmd_qemu_img(self):
        return self._which_cmd('qemu-img')

    @cached_property
    def _cmd_blkid(self):
        return self._which_cmd('blkid')

    @cached_property
    def info(self):
        for fmt in self.FORMATS:
            info = self._info(fmt)
            if info:
                return info
        raise UnknownImageFormat(self.filename)

    @property
    def format(self):
        return self.info.get('format')

    @property
    def virtual_size(self):
        return self.info.get('virtual-size')

    @property
    def real_size(self):
        return self.filepath.stat().st_size

    def _info(self, fmt):
        # we use blkid to check the 'raw' format, as qemu-img doesn't verify it
        if fmt == 'raw' and not self._is_raw_format():
            return None

        proc = subprocess.run([self._cmd_qemu_img, 'info', '--output', 'json', '-f', fmt, self.filename],
                              stdout=subprocess.PIPE,
                              stderr=subprocess.STDOUT,
                              text=True)
        return json.loads(proc.stdout) if proc.returncode == 0 else None

    def _is_raw_format(self):
        proc = subprocess.run([self._cmd_blkid, '--probe', '-o', 'export', self.filename],
                              stdout=subprocess.PIPE,
                              text=True)
        if proc.returncode != 0:
            return False
        for line in proc.stdout.split('\n'):
            k, _, v = line.strip().partition('=')
            if k == 'PTTYPE':
                return v in ['dos', 'gpt']
        return False

    def resize(self, size):
        LOGGER.info(f"Resizing '{self.filename}' from {self.virtual_size} to {size}")

        cmd = [self._cmd_qemu_img, 'resize', '-f', self.format, self.filename, str(size)]
        if self.dry_run:
            self._log_dry_run(' '.join(cmd))
            return

        proc = subprocess.run(cmd)
        if proc.returncode != 0:
            raise ImageResizeError(f"Failed to resize image '{self.filename}'")
        del self.info

    def convert(self, dest_filename, dest_format, **kwargs):
        LOGGER.info(f"Converting '{self.filename}' format {self.format} to '{dest_filename}' format {dest_format}")

        cmd = [self._cmd_qemu_img, 'convert', '-f', self.format, '-O', dest_format]
        if kwargs:
            options = ','.join([f'{k}={v}' for k, v in kwargs.items()])
            cmd += ['-o', options]
        cmd += [self.filename]

        with tempfile.TemporaryDirectory() as tempdir:
            temp_img = Path(tempdir) / 'ezaz-converted-image.img'
            cmd += [str(temp_img)]

            if self.dry_run:
                self._log_dry_run(' '.join(cmd))
            else:
                proc = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
                if proc.returncode != 0:
                    raise ImageConversionFailed(f"Failed to convert image to format '{dest_format}': {proc.stdout}")

            if self.dry_run:
                self._log_dry_run(f"move '{temp_img}' '{dest_filename}'")
            else:
                shutil.move(temp_img, dest_filename)

    def convert_to_azure_vhd(self, dest_filename):
        if self.dry_run:
            # The intermediate files won't exist, so we can't print
            # out each conversion/resizing cmdline, just abort now
            self._log_dry_run(f'Conversion to azure VHD')
            return

        # Virtual size must be a multiple of 1mb
        mb, mod = divmod(self.virtual_size, 1024 * 1024)
        if mod > 0:
            mb += 1
        dest_size = mb * 1024 * 1024

        with tempfile.TemporaryDirectory() as tempdir:
            raw_filepath = Path(tempdir) / f'ezaz-converted-image.raw'
            self.convert(raw_filepath, 'raw')

            raw_img = QemuImg(raw_filepath)
            if dest_size != raw_img.virtual_size:
                raw_img.resize(dest_size)
            raw_img.convert(dest_filename, 'vpc', subformat='fixed', force_size='on')

    @property
    def is_azure_vhd_format(self):
        # Must be VHD (called 'vpc' by qemu-img) format, virtual size
        # is multiple of 1mb, and fixed format (meaning it's a 'raw'
        # format image with a 512-byte footer)
        return all((self.format == 'vpc',
                    self.virtual_size % (1024 * 1024) == 0,
                    self.virtual_size + 512 == self.real_size))
