import shlex
import subprocess
import typing


def cmd(
    raw_command: str,
    stdout: typing.Any = subprocess.PIPE,
    stderr: typing.Any = subprocess.PIPE,
    input: typing.Union[str, None] = None,
    verbose: bool = True,
) -> subprocess.CompletedProcess:
    def vprint(string: str) -> None:
        if verbose:
            print(string)

    vprint(f"$ {raw_command}")
    command = shlex.split(raw_command)
    try:
        result = subprocess.run(
            command,
            stdout=stdout,
            stderr=stderr,
            input=input,
            encoding="utf-8",
            check=True,  # exception on non-zero code
        )
    except subprocess.CalledProcessError as e:
        vprint(e.stderr)
        raise e
    vprint(result.stdout)
    return result


def query_yes_no(question: str, default: str = "yes") -> bool:
    valid = {"yes": True, "y": True, "no": False, "n": False}
    if default is None:
        prompt = "[y/n]"
    elif default == "yes":
        prompt = "[Y/n]"
    elif default == "no":
        prompt = "[y/N]"
    else:
        raise ValueError(f'invalid default answer: "{default}"')

    while True:
        print(f"{question} {prompt}: ", end="")
        choice = input().lower()
        if default is not None and choice == "":
            return valid[default]
        elif choice in valid:
            return valid[choice]
        else:
            print(f'invalid voice "{choice}" from {[x for x in valid.keys()]}')
