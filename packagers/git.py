import json
import os
import subprocess

from utils import cmd

from packagers import AbstractPackager


class Git(AbstractPackager):
    install_dir = ""
    default_remote = ""

    def __init__(
        self,
        file_dir: str,
        file_name: str = "git_repos.json",
        install_dir: str = "",
        remote: str = "origin",
    ):
        if not install_dir:
            install_dir = os.path.join(os.path.expanduser("~"), "projects")
        self.install_dir = install_dir
        self.default_remote = remote
        super().__init__("cat {filepath}", "", "", "git --version", file_dir, file_name)

    def backup(self) -> None:
        if not os.path.isdir(self.install_dir):
            os.makedirs(self.install_dir)

        # query for all repo names and remote urls
        results = {}
        for name in os.listdir(self.install_dir):
            full_path = os.path.join(self.install_dir, name)
            if os.path.isdir(full_path):
                try:
                    remotes = (
                        cmd(f"git -C {full_path} remote").stdout.rstrip().split("\n")
                    )
                    results[name] = {
                        "remotes": {
                            remote: cmd(
                                f"git -C {full_path} remote get-url {remote}"
                            ).stdout.rstrip()
                            for remote in remotes
                        }
                    }
                except subprocess.CalledProcessError:
                    pass

        # save to backup file
        json_results = json.dumps(results, indent=4, sort_keys=True)
        with open(self.filepath, "w") as f:
            f.write(f"{json_results}\n")
        self.info()

    def restore(self) -> None:
        if not os.path.isdir(self.install_dir):
            os.makedirs(self.install_dir)
        with open(self.filepath, "r") as f:
            data = json.load(f)
            for name, conf in data.items():
                try:
                    # clone into dir
                    remotes = conf["remotes"]
                    full_path = os.path.join(self.install_dir, name)
                    default_remote = remotes[self.default_remote]
                    cmd(f"git clone {default_remote} {full_path}")

                    # setup remotes
                    for k, v in remotes.items():
                        if k != self.default_remote:
                            cmd(f"git -C {full_path} remote add {k} {v}")
                        else:
                            cmd(f"git -C {full_path} remote set-url {k} {v}")
                except subprocess.CalledProcessError:
                    pass
