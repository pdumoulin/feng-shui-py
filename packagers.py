"""Wrap shell commands to backup/restore package lists."""

import json
import os
import subprocess

from utils import cmd


class AbstractPackager(object):
    """Base packager with most common access patterns."""

    infocmd = None
    backupcmd = None
    restorecmd = None
    verifycmd = None
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
        self.infocmd = info
        self.backupcmd = backup
        self.restorecmd = restore
        self.verifycmd = verify
        self.filepath = os.path.join(file_dir, file_name)

    def verify(self):
        """Verify tool is installed."""
        cmd(self.verifycmd)

    def info(self):
        """Run info command."""
        cmd(self.infocmd.format(filepath=self.filepath))

    def backup(self):
        """Run backup command."""
        cmd(self.backupcmd.format(filepath=self.filepath))
        self.info()

    def restore(self):
        """Run restore command."""
        cmd(self.restorecmd.format(filepath=self.filepath))


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
            cmd(self.backupcmd, stdout=f)
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
            cmd(self.backupcmd, stdout=f)
            self.info()

    def restore(self):
        """Override restore to loop through each package install."""
        with open(self.filepath, 'r') as f:
            data = json.load(f)
            for k, v in data['dependencies'].items():
                package = '@'.join([k, v['version']])
                cmd(self.restorecmd.format(package=package))


class Git(AbstractPackager):
    """Manage git repos."""

    install_dir = None
    default_remote = None

    def __init__(self, file_dir, file_name='git_repos.json', install_dir=None, remote='origin'):  # noqa:E501
        """Set git specific options."""
        if not install_dir:
            install_dir = os.path.join(
                os.path.expanduser('~'),
                'projects'
            )
        self.install_dir = install_dir
        self.default_remote = remote
        super().__init__(
            'cat {filepath}',
            None,
            None,
            'git --version',
            file_dir,
            file_name
        )

    def backup(self):
        """Override backup with custom git process."""
        if not os.path.isdir(self.install_dir):
            os.makedirs(self.install_dir)

        # query for all repo names and remote urls
        results = {}
        for name in os.listdir(self.install_dir):
            full_path = os.path.join(self.install_dir, name)
            if os.path.isdir(full_path):
                try:
                    remotes = cmd(f'git -C {full_path} remote').stdout.rstrip().split('\n')  # noqa:E501
                    results[name] = {
                        'remotes': {
                            remote: cmd(f'git -C {full_path} remote get-url {remote}').stdout.rstrip()  # noqa:E501
                            for remote in remotes
                        }
                    }
                except subprocess.CalledProcessError:
                    pass

        # save to backup file
        json_results = json.dumps(results, indent=4, sort_keys=True)
        with open(self.filepath, 'w') as f:
            f.write(f'{json_results}\n')
        self.info()

    def restore(self):
        """Override restore with custom git process."""
        if not os.path.isdir(self.install_dir):
            os.makedirs(self.install_dir)
        with open(self.filepath, 'r') as f:
            data = json.load(f)
            for name, conf in data.items():
                try:
                    # clone into dir
                    remotes = conf['remotes']
                    full_path = os.path.join(self.install_dir, name)
                    default_remote = remotes[self.default_remote]
                    cmd(f'git clone {default_remote} {full_path}')

                    # setup remotes
                    for k, v in remotes.items():
                        if k != self.default_remote:
                            cmd(f'git -C {full_path} remote add {k} {v}')
                        else:
                            cmd(f'git -C {full_path} remote set-url {k} {v}')  # noqa:E501
                except subprocess.CalledProcessError:
                    pass


class Crontab(AbstractPackager):
    """Manage crontab install."""

    def __init__(self, file_dir, file_name='crontab.txt'):
        """Crontab specific options."""
        super().__init__(
            'cat {filepath}',
            'crontab -l',
            'crontab {filepath}',
            'which crontab',
            file_dir,
            file_name
        )

    def backup(self):
        """Override backup, write stdout to file."""
        with open(self.filepath, 'w') as f:
            cmd(self.backupcmd, stdout=f)
            self.info()
