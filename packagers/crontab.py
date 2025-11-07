from utils import cmd

from packagers import AbstractPackager


class Crontab(AbstractPackager):
    def __init__(self, file_dir: str, file_name: str = "crontab.txt") -> None:
        super().__init__(
            "cat {filepath}",
            "crontab -l",
            "crontab {filepath}",
            "which crontab",
            file_dir,
            file_name,
        )

    def backup(self) -> None:
        with open(self.filepath, "w") as f:
            cmd(self.backupcmd, stdout=f)
            self.info()
