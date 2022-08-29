"""Wrap shell commands to backup/restore package lists."""

import json
import os
import shlex
import subprocess


class AbstractPackager(object):
    """Base packager with most common access patterns."""

    info_cmd = None
    backup_cmd = None
    restore_cmd = None
    verify_cmd = None
    filepath = None

    def __init__(
            self,
            info, backup, restore, verify,
            file_dir, file_name):
        """Set required data.

        Args:
            info (str): command to read existing package file
            backup (str): command to create package file
            restore (str): command to install based on package file
            verify (str): command to verify tool is installed
            file_dir (str): location of package file
            file_name (str): name of package file
        """
        self.info_cmd = info
        self.backup_cmd = backup
        self.restore_cmd = restore
        self.verify_cmd = verify
        self.filepath = os.path.join(file_dir, file_name)

    def verify(self):
        """Verify tool is installed."""
        self._cmd(self.verify_cmd)

    def info(self):
        """Run info command."""
        self._cmd(self.info_cmd.format(filepath=self.filepath))

    def backup(self):
        """Run backup command."""
        self._cmd(self.backup_cmd.format(filepath=self.filepath))
        self.info()

    def restore(self):
        """Run restore command."""
        self._cmd(self.restore_cmd.format(filepath=self.filepath))

    def _cmd(
            self,
            command,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            verbose=True
            ):
        """Run shell command.

        Args:
            command (str): command to run
            stdout (subprocess.PIPE): where to capture stdout
            stderr (subprocess.PIPE): where to capture stderr
            verbose (bool): print command input and output

        Returns:
            subprocess.CompletedProcess

        Raises:
            subprocess.CalledProcessError
        """
        def vprint(string):
            if verbose:
                print(string)
        vprint(f'$ {command}')
        command = shlex.split(command)
        try:
            result = subprocess.run(
                command,
                stdout=stdout,
                stderr=stderr,
                encoding='utf-8',
                check=True  # exception on non-zero code
            )
        except subprocess.CalledProcessError as e:
            vprint(e.stderr)
            raise e
        vprint(result.stdout)
        return result


class Brew(AbstractPackager):
    """Manage mac packages via brew."""

    def __init__(self, file_dir, file_name='Brewfile'):
        """Set brew specific options."""
        super().__init__(
            'cat {filepath}',
            'brew bundle dump -f --describe --file {filepath}',
            'brew bundle install -v --no-upgrade --file {filepath}',
            'brew --version',
            file_dir,
            file_name
        )


class Apt(AbstractPackager):
    """Manage debian packages via apt-clone."""

    def __init__(self, file_dir, file_name='apt-clone.tar.gz'):
        """Set apt-clone specific options."""
        super().__init__(
            'apt-clone info {filepath}',
            'apt-clone clone {filepath}',
            'sudo apt-clone restore {filepath}',
            'apt-clone --help',
            file_dir,
            file_name
        )


class Pip(AbstractPackager):
    """Manage python packages via pip."""

    def __init__(self, file_dir, file_name='pip-freeze.txt'):
        """Set pip specific options."""
        super().__init__(
            'cat {filepath}',
            'pip freeze --no-python-version-warning',
            'pip install -r {filepath}',
            'pip --version',
            file_dir,
            file_name
        )

    def backup(self):
        """Override backup, write stdout to file."""
        with open(self.filepath, 'w') as f:
            self._cmd(self.backup_cmd, stdout=f)
            self.info()


class Npm(AbstractPackager):
    """Manage node packages via npm."""

    def __init__(self, file_dir, file_name='package.json'):
        """Set npm specific options."""
        super().__init__(
            'cat {filepath}',
            'npm list -g --json',
            'npm install -g {package}',
            'npm --version',
            file_dir,
            file_name
        )

    def backup(self):
        """Override backup, write stdout to file."""
        with open(self.filepath, 'w') as f:
            self._cmd(self.backup_cmd, stdout=f)
            self.info()

    def restore(self):
        """Override restore to loop through each package install."""
        with open(self.filepath, 'r') as f:
            data = json.load(f)
            for k, v in data['dependencies'].items():
                package = '@'.join([k, v['version']])
                self._cmd(self.restore_cmd.format(package=package))
