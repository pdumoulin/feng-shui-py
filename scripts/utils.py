"""Utility functions for scripts."""

import shlex
import subprocess


def cmd(
        command,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        verbose=True
        ):
    """Run shell command.

    Args:
        command (str): command to run
        stdout: where to send stdout
        stderr: where to send stderr
        verbose (bool): print command input and output

    """
    def vprint(string):
        if verbose:
            print(string)
    vprint(f'$ {command}')
    command = shlex.split(command)
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


def query_yes_no(question, default='yes'):
    """Query user for yes/no input."""
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
