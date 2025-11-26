from utils import cmd

from packagers import AbstractPackager

class Dconf(AbstractPackager):
    def __init__(self, file_dir: str, file_name: str = "settings.dconf") -> None:
        super().__init__(
            "cat {filepath}",
            "dconf dump /",
            "dconf load /",
            "dconf help",
            file_dir,
            file_name,
        )

    def backup(self) -> None:
        with open(self.filepath, "w") as f:
            cmd(self.backupcmd, stdout=f)
            self.info()

    def restore(self) -> None:
        with open(self.filepath, "r") as f:
            cmd(self.restorecmd, input=f.read())
