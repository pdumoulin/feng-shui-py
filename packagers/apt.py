
from packagers import AbstractPackager

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
