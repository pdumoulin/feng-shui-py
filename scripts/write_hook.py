#!/usr/bin/python3
"""Perform action when saving file matching pattern(s)."""

import os
import re
import sys
import time
from subprocess import call

# 0 => regex to match file path
# 1 => command to run, substituting matched groups by index using $N
CONFIG = [
    (
        '^(~/projects/collab/pdumoulin/lambda-ecr-poc/).*\\.py$',
        'cd $0 && docker-compose restart fibcow || docker-compose up -d --build fibcow'  # noqa:E501
    ),
    (
        '^(~/projects/collab/pdumoulin/lambda-ecr-poc/).*\\.(yml|yaml)$',
        'cd $0 && docker-compose up -d --build fibcow'
    ),
    (
        '^(~/projects/collab/pdumoulin/aws-step-functions-local/)lambda/(.*?)/.*\\.py$',  # noqa:E501
        'cd $0 && docker-compose restart > /dev/null 2>&1 &'
    ),
    (
        '^(~/projects/lambda-.*?/lambda/.*?/)src/.*\\.py$',
        'cd $0 && docker-compose restart function > /dev/null 2>&1 &'
    ),
    (
        '^(~/projects/.*?/).*\\.py$',
        'touch -c $0app.py'
    ),
    (
        '^(~/tarantula/).*\\.py$',
        'touch -c $0web.py'
    )
]


def main():
    """Entrypoint."""
    start_time = time.time()

    # full file path being saved
    file_path = sys.argv[1]

    # expand homedir and add defaults
    config = load_config(CONFIG)

    # match regex and compile action command to run
    matches = match_config(file_path, config)

    # run the tasks
    for regex, action in matches:
        print(f'! {regex}')
        print(f'$ {action}')
        call(action, shell=True)

    # output on runtime and configs matched
    print(f'Took {time.time() - start_time} seconds')
    print(f'Matched {len(matches)} config(s)')


def match_config(file_path, config):
    """Match dir regex and replace matching groups in action."""
    actions = []
    for regex, action in config:

        # match regex to file path
        match = re.match(regex, file_path)
        if match:

            # replace $N placeholders in action with regex groups
            for idx, group in enumerate(match.groups()):
                action = action.replace(f'${idx}', group)
            actions.append((regex, action))

    return actions


def load_config(config):
    """Normalize dir path and expand home dir."""
    result = []
    home_char = '~'
    for regex, action in config:

        # remove duplicate seperators
        norm_path = os.path.normpath(regex)

        # expand home dir
        ex_path = os.path.expanduser(norm_path[norm_path.find(home_char):])

        # combine expanded home dir back to regex
        final_path = norm_path.split(home_char)[0] + ex_path

        # add back config with modified regex
        result.append((final_path, action))

    return result


if __name__ == '__main__':
    main()
