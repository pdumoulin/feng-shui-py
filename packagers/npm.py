import json

from utils import cmd

from packagers import AbstractPackager


class Npm(AbstractPackager):
    def __init__(self, file_dir: str, file_name: str = "package.json") -> None:
        super().__init__(
            "cat {filepath}",
            "npm list -g --json",
            "npm install -g {package}",
            "npm --version",
            file_dir,
            file_name,
        )

    def backup(self) -> None:
        with open(self.filepath, "w") as f:
            cmd(self.backupcmd, stdout=f)
            self.info()

    def restore(self) -> None:
        with open(self.filepath, "r") as f:
            data = json.load(f)
            for k, v in data["dependencies"].items():
                package = "@".join([k, v["version"]])
                cmd(self.restorecmd.format(package=package))
