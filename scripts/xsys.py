"""Cross platform command wrapper."""

import platform
import sys

import utils

# configuration for mapping commands cross env
commands = {
    'copy': {
        'linux': 'xclip -i',
        'darwin': 'pbcopy',
        'windows': 'clip'
    },
    'paste': {
        'linux': 'xclip -o',
        'darwin': 'pbpaste',
        'windows': 'paste'
    }
}
options = commands.keys()
options_str = '|'.join(options)

# operating system type identifier
plat = platform.system().lower()

# read in command name
if len(sys.argv) == 1:
    exit(f'ARGV[1] command must be one of "{options_str}"')
command = sys.argv[1]

# verify command is supported
if command not in options:
    exit(f'command "{command}" not in supported commands "{options_str}"!')

# check if platform support command
if plat not in commands[command]:
    exit(f'platform "{plat}" not supported for command "{command}"')

# run the command
utils.cmd(commands[command][plat], stdout=None, stderr=None, verbose=False)
