#!/usr/bin/python3
"""Perform action when saving file matching pattern in dir."""

import os
import sys
import time
from subprocess import call

# key: directory to watch, inclusing sub dirs
# value:
#   extensions    : list of file extensions to monitor for changes (default: *)
#   action        : command to run if matched (default: echo noop)
#   sub_dir_level : num dirs to move up before running command (default 0)
CONFIG = {
    '~/projects/collab/pdumoulin/lambda-ecr-poc': {
        'extensions': ['py'],
        'action': 'docker-compose restart fibcow || docker-compose up -d fibcow'  # noqa:E501
    },
    '~/projects/': {
        'extensions': ['py'],
        'action': 'touch -c app.py',
        'sub_dir_level': 1
    }
}


def main():
    """Entrypoint."""
    start_time = time.time()

    # full file path being saved
    file_path = sys.argv[1]

    # load config, expand directory paths
    config = load_config()

    # only include configs matching file location and extension
    filtered_config = filter_config(file_path, config)

    # run commands in dirs according to config
    for run_dir, action in generate_tasks(file_path, filtered_config):
        cmd = f'cd {run_dir} && {action} ; cd --'
        print(f'$ {cmd}')
        call(cmd, shell=True)

    # output on runtime and configs matched
    print(f'Took {time.time() - start_time} seconds')
    print(f'Matched {len(filtered_config.keys())} config(s)')


def run_path(file_path, dir_path, num_levels):
    """Walk up num levels from dir path into file path."""
    if num_levels == 0:
        return dir_path
    dir_len = len(dir_path.split(os.sep))
    sub_dir_parts = file_path.split(os.sep)[dir_len:][:num_levels]
    return os.path.join(dir_path, *sub_dir_parts)


def generate_tasks(file_path, config):
    """Parse config to generate commands and dirs to run them in."""
    return [
        (
            run_path(file_path, directory, setup.get('sub_dir_level')),
            setup['action']
        )
        for directory, setup in config.items()
    ]


def file_in_dir(file_path, dir_path):
    """File is in dir according to path."""
    return file_path.startswith(dir_path)


def extension_matches(file_path, extensions):
    """Filepath matches allow list of extensions."""
    return extensions == '*' or any([file_path.endswith(f'.{x}') for x in extensions])  # noqa:E501


def filter_config(file_path, config):
    """Match config blocks relevant to file path."""
    return {
        k: v for k, v in config.items()
        if file_in_dir(file_path, k)
        and extension_matches(file_path, v['extensions'])
    }


def load_config():
    """Normailize dir paths and fill in default configs."""
    return {
        os.path.expanduser(os.path.normpath(k)): {
            'extensions': v.get('extensions', '*'),
            'action': v.get('action', 'echo noop'),
            'sub_dir_level': v.get('sub_dir_level', 0)
        } for k, v in CONFIG.items()
    }


if __name__ == '__main__':
    main()
