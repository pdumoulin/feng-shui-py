"""Open two sibling files from mirrored dirs side-by-side."""

import os
import sys

import utils

# names of sibling mirror directories
SPLITS = ('qa', 'prod')

# filename to find sibling of
filename = sys.argv[1]
cwd = os.getcwd()

# get full file path
file_path = os.path.join(cwd, filename)
split_path = file_path.split(os.path.sep)

# check if file exists
if not os.path.isfile(file_path):
    exit(f'Unable to find file {file_path}')

# determine how to find sibling file
count_one = split_path.count(SPLITS[0])
count_two = split_path.count(SPLITS[1])

# fatal error trying to find sibling file
if (count_one + count_two) != 1:
    exit(f'Unable to interpret replacements for {file_path} with {SPLITS[0]} == {count_one} and {SPLITS[1]} == {count_two}')  # noqa:E501

# find value to switch to find mirrored file
base_value = SPLITS[0] if count_one else SPLITS[1]
switch_value = SPLITS[0] if count_two else SPLITS[1]

# replace base value with switch value
split_path[split_path.index(base_value)] = switch_value
sib_file_path = os.path.sep.join(split_path)

# open both files in vsplit
utils.cmd(f'vi {file_path} {sib_file_path} -O', stdout=None, stderr=None)
