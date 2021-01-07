#!/usr/bin/python3
"""Perform action when saving file matching pattern in dir."""

import os
import sys
import time
from subprocess import call


def main():
    """Entrypoint."""
    start_time = time.time()

    # file being saved
    file_name = sys.argv[1]

    # take action when files matching pattern are modified in dir
    config = {
        '~/projects/collab/pdumoulin/lambda-ecr-poc': {
            'extensions': ['py'],
            'action': 'docker-compose restart fibcow'
        },
        '~/projects/': {
            'extensions': ['py'],
            'action': 'touch -c app.py',
            'sub_dir_level': 1
        }
    }

    # loop through config, looking for actions to take
    for directory, setup in config.items():
        directory = os.path.normpath(directory)

        # make sure file paths are absolute
        if directory.startswith('~'):
            directory = directory.replace('~', os.path.expanduser('~'))

        # check if file being saved is in config setting
        if file_name.startswith(directory):

            # calculate directory to run command in, moving up dirs if needed
            sub_dir_level = setup.get('sub_dir_level', 0)
            dir_len = len(directory.split(os.sep))
            sub_dir_parts = file_name.split(os.sep)[dir_len:][:sub_dir_level]
            run_dir = os.path.join(directory, *sub_dir_parts)

            # check if file extension is being watched
            if any([file_name.endswith(x) for x in setup['extensions']]):
                cmd = f"cd {run_dir} && {setup['action']} ; cd --"
                print(f'$ {cmd}')
                call(cmd, shell=True)

    # output on runtime
    elapsed = time.time() - start_time
    print(f'Took {elapsed} seconds')


if __name__ == '__main__':
    main()
