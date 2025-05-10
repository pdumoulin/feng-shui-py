"""Utility functions for scripts."""

import shlex
import subprocess
import typing


def cmd(
        raw_command: str,
        stdout: typing.Any = subprocess.PIPE,
        stderr: typing.Any = subprocess.PIPE,
        verbose: bool = True
        ) -> subprocess.CompletedProcess:
    """Run shell command.

    Args:
        command (str): command to run
        stdout (subprocess.PIPE): where to capture stdout
        stderr (subprocess.PIPE): where to capture stderr
        verbose (bool): print command input and output

    Returns:
        subprocess.CompletedProcess

    Raises:
        subprocess.CalledProcessError
    """
    def vprint(string: str) -> None:
        if verbose:
            print(string)
    vprint(f'$ {raw_command}')
    command = shlex.split(raw_command)
    try:
        result = subprocess.run(
            command,
            stdout=stdout,
            stderr=stderr,
            encoding='utf-8',
            check=True  # exception on non-zero code
        )
    except subprocess.CalledProcessError as e:
        vprint(e.stderr)
        raise e
    vprint(result.stdout)
    return result


def query_yes_no(question: str, default: str = 'yes') -> bool:
    """Query user for yes/no input.

    Args:
        question (str): prompt for user
        default (str): set option with if no user input

    Returns:
        bool: user selection
    """
    valid = {
        'yes': True,
        'y': True,
        'no': False,
        'n': False
    }
    if default is None:
        prompt = '[y/n]'
    elif default == 'yes':
        prompt = '[Y/n]'
    elif default == 'no':
        prompt = '[y/N]'
    else:
        raise ValueError(f'invalid default answer: "{default}"')

    while True:
        print(f'{question} {prompt}: ', end='')
        choice = input().lower()
        if default is not None and choice == '':
            return valid[default]
        elif choice in valid:
            return valid[choice]
        else:
            print(f'invalid voice "{choice}" from {[x for x in valid.keys()]}')
