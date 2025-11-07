from utils import cmd

from packagers import AbstractPackager


class Pipx(AbstractPackager):
    def __init__(self, file_dir: str, file_name: str = "pipx.json") -> None:
        super().__init__(
            "cat {filepath}",
            "pipx list --include-injected --json",
            "pipx install-all {filepath}",
            "pipx --version",
            file_dir,
            file_name,
        )

    def backup(self) -> None:
        with open(self.filepath, "w") as f:
            cmd(self.backupcmd, stdout=f)
            self.info()
