#!/usr/bin/python3
"""Perform action when saving file matching pattern in dir."""

import os
import re
import sys
import time
from subprocess import call

# key: regex to match file path
#   action: command to perform on match
#   dir_index: zero-ed index of dir to run command in
CONFIG = {
    '~/projects/collab/pdumoulin/lambda-ecr-poc/.*py$': {
        'action': 'docker-compose restart fibcow || docker-compose up -d --build fibcow',  # noqa:E501
        'dir_index': 3
    },
    '~/projects/collab/pdumoulin/lambda-ecr-poc/.*\\.(yml|yaml)$': {
        'action': 'docker-compose up -d --build fibcow',
        'dir_index': 3
    },
    '~/projects/.*\\.py$': {
        'action': 'touch -c app.py',
        'dir_index': 1
    },
    '~/tarantula/.*\\.py$': {
        'action': 'touch -c web.py',
        'dir_index': 0
    }
}


def main():
    """Entrypoint."""
    start_time = time.time()

    # full file path being saved
    file_path = sys.argv[1]

    # expand homedir and add defaults
    config = load_config(CONFIG)

    # filter out non-matching rules
    config = filter_config(file_path, config)

    # dir & action tupe of tasks to run
    tasks = generate_tasks(file_path, config)

    # run commands in dirs according to config
    for run_dir, action in tasks:
        cmd = f'cd {run_dir} && {action} ; cd --'
        print(f'$ {cmd}')
        call(cmd, shell=True)

    # output on runtime and configs matched
    print(f'Took {time.time() - start_time} seconds')
    print(f'Matched {len(config.keys())} config(s)')


def sub_path(file_path, index):
    """Truncate file path based on number of dirs."""
    split_path = file_path.split(os.path.sep)[:index + 2]
    return os.path.join(os.path.sep, *split_path)


def generate_tasks(file_path, config):
    """Parse config to generate commands and dirs to run them in."""
    return [
        (
            sub_path(file_path, setup['dir_index']),
            setup['action']
        )
        for _, setup in config.items()
    ]


def filter_config(file_path, config):
    """Filter out non-matching dir patterns."""
    return {
        k: v for k, v in config.items()
        if re.match(k, file_path)
    }


def load_config(config):
    """Expand dir pattern and take into account homedir expansion for index."""
    result = {}
    for k, v in config.items():
        norm_path = os.path.normpath(k)
        ex_path = os.path.expanduser(norm_path)
        path_diff = ex_path.count(os.path.sep) - norm_path.count(os.path.sep)
        v['dir_index'] += path_diff
        result[ex_path] = v
    return result


if __name__ == '__main__':
    main()
