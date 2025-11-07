from packagers import AbstractPackager


class Brew(AbstractPackager):
    def __init__(self, file_dir: str, file_name: str = "Brewfile"):
        super().__init__(
            "cat {filepath}",
            "brew bundle dump -f --describe --file {filepath}",
            "brew bundle install -v --no-upgrade --file {filepath}",
            "brew --version",
            file_dir,
            file_name,
        )


class Apt(AbstractPackager):
    def __init__(self, file_dir: str, file_name: str = "apt-clone.tar.gz") -> None:
        super().__init__(
            "apt-clone info {filepath}",
            "apt-clone clone {filepath}",
            "sudo apt-clone restore {filepath}",
            "apt-clone --help",
            file_dir,
            file_name,
        )
