#!/usr/bin/python3

"""Touch auto-reload file when saving another file."""

import os
import sys
import time
from subprocess import call

start_time = time.time()

# file being saved
file_name = sys.argv[1]

# directory to monitor for project changes
project_dir = os.getenv(
    'PROJECT_DIR',
    os.path.join(os.path.expanduser('~'), 'projects')
)

# is file in dir being watched
if file_name.startswith(project_dir):

    # determine project name and dir touched file is in
    project_name = file_name.split(os.path.sep)[
        len(project_dir.split(os.path.sep))
    ]
    project_location = os.path.join(project_dir, project_name)

    # determine what file to touch to trigger a reload
    custom_touch_files = {}
    default_file_name = os.path.join('src', 'app.py')
    reload_file_name = custom_touch_files.get(project_name, default_file_name)
    reload_file_path = os.path.join(project_location, reload_file_name)

    # touch file to trigger app restart
    if os.path.isfile(reload_file_path):
        call(f'touch {reload_file_path}', shell=True)
    else:
        print(f'{reload_file_path}" is not valid file')
else:
    print(f'File "{file_name}" not in "{project_dir}"')

# output on slow-ness
elapsed = time.time() - start_time
print(f'Took {elapsed} seconds')
