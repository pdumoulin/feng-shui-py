
import os

from packagers import AbstractPackager
from packagers.exceptions import SudoException

try:
    import apt
except ModuleNotFoundError:
    pass

class Apt(AbstractPackager):
    def __init__(self, file_dir: str, file_name: str = "apt.txt") -> None:
        super().__init__(
            "cat {filepath}",
            "",
            "",
            "dpkg -s python3-apt",
            file_dir,
            file_name,
        )

    def backup(self) -> None:
        try:
            cache = apt.cache.Cache()
            cache.update()
            cache.open()
            manual = [
                pkg.name
                for pkg in cache
                if pkg.is_installed and not pkg.is_auto_installed
            ]
            with open(self.filepath, "w") as f:
                f.write(os.linesep.join(manual))
            self.info()
        except apt.cache.LockFailedException:
            raise SudoException()

    def restore(self) -> None:
        try:
            with open(self.filepath, "r") as f:
                packages = [line.strip() for line in f.readlines()]
            cache = apt.cache.Cache()
            cache.update()
            cache.open()
            with cache.actiongroup():
                for package in [cache[x] for x in packages]:
                    if not package.is_installed:
                        package.mark_install()
            cache.commit()
        except apt.cache.LockFailedException:
            raise SudoException()
