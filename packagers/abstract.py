import os

from utils import cmd


class AbstractPackager(object):
    infocmd = ""
    backupcmd = ""
    restorecmd = ""
    verifycmd = ""
    filepath = ""

    def __init__(
        self,
        info: str,
        backup: str,
        restore: str,
        verify: str,
        file_dir: str,
        file_name: str,
    ) -> None:
        self.infocmd = info
        self.backupcmd = backup
        self.restorecmd = restore
        self.verifycmd = verify
        self.filepath = os.path.join(file_dir, file_name)

    def verify(self) -> None:
        cmd(self.verifycmd)

    def info(self) -> None:
        cmd(self.infocmd.format(filepath=self.filepath))

    def backup(self) -> None:
        cmd(self.backupcmd.format(filepath=self.filepath))
        self.info()

    def restore(self) -> None:
        cmd(self.restorecmd.format(filepath=self.filepath))
