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
    touch_files = {
        'portal-api': 'platform.wsgi',
        'default': 'src%sapp.py' % os.path.sep
    }
    reload_file_name = touch_files['default']\
        if project_name not in touch_files.keys()\
        else touch_files[project_name]
    reload_file_path = os.path.join(project_location, reload_file_name)

    # touch file to trigger app restart
    if os.path.isfile(reload_file_path):
        call('touch %s' % (reload_file_path), shell=True)
    else:
        print('"%s" is not valid file' % reload_file_path)

    # output on slow-ness
    elapsed = time.time() - start_time
    print('Took %s seconds' % elapsed)
